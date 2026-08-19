"""
Music Queue and Guild Player State Manager for Gandiva Tunes.
Handles real-time progress timing, queue loop modes, auto-disconnect, and persistent panel updates.
Credits: Syko Reddy
"""

import asyncio
import time
import random
import discord
from typing import Dict, List, Optional, Any
from config import DEFAULT_VOLUME, IDLE_TIMEOUT
from database.db_manager import db_manager
from utils.music_engine import MusicEngine
from utils.ui_theme import create_now_playing_embed, create_setup_idle_embed


class GuildPlayer:
    def __init__(self, bot: discord.Client, guild: discord.Guild):
        self.bot = bot
        self.guild = guild
        self.voice_client: Optional[discord.VoiceClient] = None
        self.queue: List[Dict[str, Any]] = []
        self.history: List[Dict[str, Any]] = []
        self.current_track: Optional[Dict[str, Any]] = None
        
        # Audio Settings
        self.volume: int = DEFAULT_VOLUME
        self.loop_mode: str = "OFF" # "OFF", "TRACK", "QUEUE"
        self.filter_name: str = "Normal"
        self.is_247: bool = False
        
        # Timing / Progress Tracking
        self.start_time: float = 0.0
        self.pause_start_time: float = 0.0
        self.total_paused_duration: float = 0.0
        self.is_paused: bool = False
        
        # Messages & Tasks
        self.now_playing_message: Optional[discord.Message] = None
        self.idle_task: Optional[asyncio.Task] = None
        self.progress_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    @property
    def is_playing(self) -> bool:
        return self.voice_client and self.voice_client.is_playing()

    def get_current_position(self) -> int:
        """Calculate elapsed playback seconds accurately."""
        if not self.current_track or self.start_time == 0:
            return 0
        if self.is_paused:
            elapsed = self.pause_start_time - self.start_time - self.total_paused_duration
        else:
            elapsed = time.monotonic() - self.start_time - self.total_paused_duration
        return max(0, int(elapsed))

    async def add_track(self, track: Dict[str, Any], play_now_if_idle: bool = True):
        """Add single track to queue."""
        self.queue.append(track)
        self._cancel_idle_timer()
        if play_now_if_idle and not self.is_playing and not self.is_paused and not self.current_track:
            await self.play_next()
        else:
            await self.update_setup_panel()

    async def add_tracks(self, tracks: List[Dict[str, Any]]):
        """Add multiple tracks (e.g. from playlist)."""
        self.queue.extend(tracks)
        self._cancel_idle_timer()
        if not self.is_playing and not self.is_paused and not self.current_track:
            await self.play_next()
        else:
            await self.update_setup_panel()

    async def play_next(self, restart_current: bool = False):
        """Play the next track from the queue or handle repeat/loop logic."""
        async with self._lock:
            # Check Voice Client
            if not self.voice_client or not self.voice_client.is_connected():
                self.voice_client = self.guild.voice_client
                if not self.voice_client:
                    return

            # Loop Modes
            if restart_current and self.current_track:
                next_song = self.current_track
            elif self.loop_mode == "TRACK" and self.current_track:
                next_song = self.current_track
            elif self.loop_mode == "QUEUE" and self.current_track:
                self.queue.append(self.current_track)
                next_song = self.queue.pop(0) if self.queue else None
            else:
                if self.current_track:
                    self.history.append(self.current_track)
                next_song = self.queue.pop(0) if self.queue else None

            if not next_song:
                self.current_track = None
                self._stop_progress_tracker()
                await self.update_setup_panel()
                self._start_idle_timer()
                return

            self.current_track = next_song
            self.start_time = time.monotonic()
            self.total_paused_duration = 0.0
            self.is_paused = False

            # Refresh stream URL if needed
            stream_url = await MusicEngine.get_fresh_stream_url(next_song)
            try:
                source = MusicEngine.create_audio_source(
                    stream_url,
                    filter_name=self.filter_name,
                    volume=self.volume,
                )
            except Exception as e:
                print(f"Error creating audio source: {e}")
                # Skip to next song
                self.bot.loop.create_task(self.play_next())
                return

            def after_playing(error):
                if error:
                    print(f"Audio playback error: {error}")
                fut = asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop)
                try:
                    fut.result()
                except Exception:
                    pass

            if self.voice_client.is_playing() or self.voice_client.is_paused():
                self.voice_client.stop()

            self.voice_client.play(source, after=after_playing)
            self._start_progress_tracker()
            await self.update_setup_panel()

    def pause(self) -> bool:
        """Pause playback."""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            self.is_paused = True
            self.pause_start_time = time.monotonic()
            self.bot.loop.create_task(self.update_setup_panel())
            return True
        return False

    def resume(self) -> bool:
        """Resume playback."""
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            self.is_paused = False
            if self.pause_start_time > 0:
                self.total_paused_duration += time.monotonic() - self.pause_start_time
            self.bot.loop.create_task(self.update_setup_panel())
            return True
        return False

    def skip(self) -> bool:
        """Skip current track."""
        if self.voice_client and (self.voice_client.is_playing() or self.voice_client.is_paused()):
            # Temporarily bypass single track loop on manual skip
            prev_mode = self.loop_mode
            if self.loop_mode == "TRACK":
                self.loop_mode = "OFF"
            self.voice_client.stop()
            self.loop_mode = prev_mode
            return True
        return False

    def stop(self):
        """Stop music, clear queue, and reset state."""
        self.queue.clear()
        self.current_track = None
        self._stop_progress_tracker()
        if self.voice_client and (self.voice_client.is_playing() or self.voice_client.is_paused()):
            self.voice_client.stop()
        self.bot.loop.create_task(self.update_setup_panel())
        self._start_idle_timer()

    def set_volume(self, volume: int):
        """Set volume (0 - 150%)."""
        self.volume = max(0, min(volume, 150))
        if self.voice_client and self.voice_client.source:
            if isinstance(self.voice_client.source, discord.PCMVolumeTransformer):
                self.voice_client.source.volume = self.volume / 100.0
        self.bot.loop.create_task(self.update_setup_panel())

    async def change_filter(self, filter_name: str):
        """Change equalizer/audio filter on the fly."""
        self.filter_name = filter_name
        if self.current_track and self.voice_client:
            # Re-create source with filter at current position
            await self.play_next(restart_current=True)

    def shuffle(self):
        """Shuffle queue."""
        if self.queue:
            random.shuffle(self.queue)
            self.bot.loop.create_task(self.update_setup_panel())

    def toggle_loop(self) -> str:
        """Cycle through OFF -> TRACK -> QUEUE -> OFF."""
        if self.loop_mode == "OFF":
            self.loop_mode = "TRACK"
        elif self.loop_mode == "TRACK":
            self.loop_mode = "QUEUE"
        else:
            self.loop_mode = "OFF"
        self.bot.loop.create_task(self.update_setup_panel())
        return self.loop_mode

    # ----------------- PROGRESS & PANEL UPDATE TASKS -----------------

    def _start_progress_tracker(self):
        self._stop_progress_tracker()
        self.progress_task = self.bot.loop.create_task(self._progress_update_loop())

    def _stop_progress_tracker(self):
        if self.progress_task and not self.progress_task.done():
            self.progress_task.cancel()
            self.progress_task = None

    async def _progress_update_loop(self):
        """Periodically update the panel progress timing every 8 seconds."""
        try:
            while self.current_track and self.voice_client and self.voice_client.is_connected():
                await asyncio.sleep(8)
                if not self.is_paused:
                    await self.update_setup_panel()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Progress update loop error: {e}")

    async def update_setup_panel(self):
        """Update the dedicated #gandiva-tunes-music controller message."""
        try:
            channel_id, message_id = await db_manager.get_music_channel(self.guild.id)
            if not channel_id or not message_id:
                return

            channel = self.guild.get_channel(channel_id)
            if not channel:
                return

            try:
                message = await channel.fetch_message(message_id)
            except discord.NotFound:
                return
            except discord.Forbidden:
                return

            from utils.views import MusicControlView

            # Check 24/7 setting from DB
            self.is_247 = await db_manager.get_247(self.guild.id)

            if self.current_track:
                embed = create_now_playing_embed(
                    track=self.current_track,
                    current_pos=self.get_current_position(),
                    is_paused=self.is_paused,
                    volume=self.volume,
                    loop_mode=self.loop_mode,
                    filter_name=self.filter_name,
                    is_247=self.is_247,
                    queue_len=len(self.queue),
                )
                view = MusicControlView(self)
                await message.edit(embed=embed, view=view)
            else:
                prefix = await db_manager.get_prefix(self.guild.id)
                embed = create_setup_idle_embed(prefix=prefix)
                view = MusicControlView(self)
                await message.edit(embed=embed, view=view)
        except Exception as e:
            # Catch transient network errors or rate-limits silently
            pass

    # ----------------- IDLE / 24/7 AUTO-DISCONNECT -----------------

    def _start_idle_timer(self):
        self._cancel_idle_timer()
        self.idle_task = self.bot.loop.create_task(self._idle_timeout_handler())

    def _cancel_idle_timer(self):
        if self.idle_task and not self.idle_task.done():
            self.idle_task.cancel()
            self.idle_task = None

    async def _idle_timeout_handler(self):
        """Disconnect from voice channel after idle timeout unless 24/7 is enabled."""
        if IDLE_TIMEOUT <= 0:
            return
        try:
            await asyncio.sleep(IDLE_TIMEOUT)
            is_247 = await db_manager.get_247(self.guild.id)
            if is_247:
                return # Stay connected 24/7
            
            if self.voice_client and not self.is_playing and not self.current_track:
                await self.voice_client.disconnect(force=True)
                self.voice_client = None
                await self.update_setup_panel()
        except asyncio.CancelledError:
            pass


# Guild player cache
_players: Dict[int, GuildPlayer] = {}


def get_player(bot: discord.Client, guild: discord.Guild) -> GuildPlayer:
    """Retrieve or create the GuildPlayer for a guild."""
    if guild.id not in _players:
        _players[guild.id] = GuildPlayer(bot, guild)
    return _players[guild.id]


def cleanup_player(guild_id: int):
    """Remove and cleanup player for a guild."""
    if guild_id in _players:
        player = _players.pop(guild_id)
        player.stop()
