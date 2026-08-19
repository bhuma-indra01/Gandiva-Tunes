"""
Core Music Commands Cog for Gandiva Tunes Discord Music Bot.
Supports Hybrid Slash & Prefix commands with Neon Glassmorphic embeds.
Credits: Syko Reddy
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, Literal
from utils.music_queue import get_player
from utils.music_engine import MusicEngine
from utils.ui_theme import (
    create_now_playing_embed,
    create_queue_embed,
    create_success_embed,
    create_error_embed,
    format_duration,
)
from utils.views import MusicControlView, QueuePaginationView


class MusicCog(commands.Cog, name="Music"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _ensure_voice(self, ctx: commands.Context) -> bool:
        """Helper to ensure user and bot are in appropriate voice channels."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.reply(
                embed=create_error_embed(
                    "Voice Connection Required",
                    "You must be connected to a voice channel to use music commands.",
                ),
                ephemeral=True,
            )
            return False

        user_channel = ctx.author.voice.channel
        if not ctx.guild.voice_client:
            try:
                await user_channel.connect(timeout=20.0, reconnect=True)
            except Exception as e:
                await ctx.reply(
                    embed=create_error_embed("Voice Connection Failed", f"Could not join voice channel: {e}"),
                    ephemeral=True,
                )
                return False
        elif ctx.guild.voice_client.channel != user_channel:
            try:
                await ctx.guild.voice_client.move_to(user_channel)
            except Exception:
                pass

        return True

    @commands.hybrid_command(
        name="play",
        aliases=["p"],
        description="Plays a song or playlist from YouTube, Spotify, SoundCloud, or direct URLs.",
    )
    @app_commands.describe(query="Song title, YouTube URL, or Spotify track/playlist/album link")
    async def play(self, ctx: commands.Context, *, query: str):
        """Play a song or add it to queue."""
        if not await self._ensure_voice(ctx):
            return

        await ctx.defer()
        player = get_player(self.bot, ctx.guild)
        player.voice_client = ctx.guild.voice_client

        try:
            tracks = await MusicEngine.extract_info(query, requester=ctx.author)
            if not tracks:
                await ctx.reply(
                    embed=create_error_embed("No Results Found", f"Could not find any songs for `{query}`.")
                )
                return

            if len(tracks) == 1:
                track = tracks[0]
                await player.add_track(track)
                await ctx.reply(
                    embed=create_success_embed(
                        "Track Enqueued",
                        f"🎵 **[{track.get('title')}]({track.get('url')})** `[{format_duration(track.get('duration', 0))}]`\n"
                        f"Requested by {ctx.author.mention}",
                    )
                )
            else:
                await player.add_tracks(tracks)
                await ctx.reply(
                    embed=create_success_embed(
                        "Playlist Enqueued",
                        f"📂 Loaded **{len(tracks)} tracks** into queue!\nRequested by {ctx.author.mention}",
                    )
                )
        except Exception as e:
            await ctx.reply(
                embed=create_error_embed("Playback Error", f"An error occurred while loading audio: {e}")
            )

    @commands.hybrid_command(name="pause", description="Pauses current music playback.")
    async def pause(self, ctx: commands.Context):
        """Pause playback."""
        player = get_player(self.bot, ctx.guild)
        if player.pause():
            await ctx.reply(embed=create_success_embed("Playback Paused", "⏸️ Music has been paused."))
        else:
            await ctx.reply(
                embed=create_error_embed("Cannot Pause", "No active track playing to pause."),
                ephemeral=True,
            )

    @commands.hybrid_command(name="resume", aliases=["unpause"], description="Resumes paused music playback.")
    async def resume(self, ctx: commands.Context):
        """Resume playback."""
        player = get_player(self.bot, ctx.guild)
        if player.resume():
            await ctx.reply(embed=create_success_embed("Playback Resumed", "▶️ Music is now playing."))
        else:
            await ctx.reply(
                embed=create_error_embed("Cannot Resume", "Music is not paused."),
                ephemeral=True,
            )

    @commands.hybrid_command(name="skip", aliases=["s", "next"], description="Skips the currently playing song.")
    async def skip(self, ctx: commands.Context):
        """Skip current track."""
        player = get_player(self.bot, ctx.guild)
        if player.skip():
            await ctx.reply(embed=create_success_embed("Track Skipped", "⏭️ Skipped to next track."))
        else:
            await ctx.reply(
                embed=create_error_embed("Cannot Skip", "No track is currently playing."),
                ephemeral=True,
            )

    @commands.hybrid_command(name="stop", description="Stops music playback and clears the entire queue.")
    async def stop(self, ctx: commands.Context):
        """Stop music and clear queue."""
        player = get_player(self.bot, ctx.guild)
        player.stop()
        await ctx.reply(
            embed=create_success_embed("Music Stopped", "⏹️ Playback stopped and queue cleared.")
        )

    @commands.hybrid_command(name="nowplaying", aliases=["np"], description="Shows detailed information about the current track.")
    async def now_playing(self, ctx: commands.Context):
        """Show now playing embed with live progress timing."""
        player = get_player(self.bot, ctx.guild)
        if not player.current_track:
            await ctx.reply(
                embed=create_error_embed("Nothing Playing", "No music is currently playing."),
                ephemeral=True,
            )
            return

        embed = create_now_playing_embed(
            track=player.current_track,
            current_pos=player.get_current_position(),
            is_paused=player.is_paused,
            volume=player.volume,
            loop_mode=player.loop_mode,
            filter_name=player.filter_name,
            is_247=player.is_247,
            queue_len=len(player.queue),
        )
        view = MusicControlView(player)
        await ctx.reply(embed=embed, view=view)

    @commands.hybrid_command(name="queue", aliases=["q"], description="Displays the current server music queue.")
    @app_commands.describe(page="Queue page number to view (default 1)")
    async def queue_cmd(self, ctx: commands.Context, page: int = 1):
        """Show current song queue."""
        player = get_player(self.bot, ctx.guild)
        embed = create_queue_embed(
            queue_list=player.queue,
            current_track=player.current_track,
            page=page,
            per_page=10,
        )
        view = QueuePaginationView(player, current_page=page)
        await ctx.reply(embed=embed, view=view)

    @commands.hybrid_command(name="volume", aliases=["vol", "v"], description="Adjusts playback volume (0% to 150%).")
    @app_commands.describe(level="Volume percentage from 0 to 150")
    async def volume_cmd(self, ctx: commands.Context, level: int):
        """Set volume level."""
        if not (0 <= level <= 150):
            await ctx.reply(
                embed=create_error_embed("Invalid Volume", "Please choose a volume level between `0` and `150`."),
                ephemeral=True,
            )
            return

        player = get_player(self.bot, ctx.guild)
        player.set_volume(level)
        await ctx.reply(
            embed=create_success_embed("Volume Changed", f"🔊 Volume set to **{level}%**.")
        )

    @commands.hybrid_command(name="loop", description="Sets loop mode (off, track, queue).")
    @app_commands.describe(mode="Choose loop mode")
    async def loop_cmd(
        self,
        ctx: commands.Context,
        mode: Optional[Literal["off", "track", "queue"]] = None,
    ):
        """Toggle or set repeat mode."""
        player = get_player(self.bot, ctx.guild)
        if mode:
            player.loop_mode = mode.upper()
            await player.update_setup_panel()
            new_mode = player.loop_mode
        else:
            new_mode = player.toggle_loop()

        labels = {"OFF": "Disabled", "TRACK": "Single Track", "QUEUE": "Entire Queue"}
        await ctx.reply(
            embed=create_success_embed("Loop Mode", f"🔁 Loop mode set to: **{labels.get(new_mode, new_mode)}**")
        )

    @commands.hybrid_command(name="shuffle", description="Shuffles all songs in the queue randomly.")
    async def shuffle_cmd(self, ctx: commands.Context):
        """Randomly shuffle songs."""
        player = get_player(self.bot, ctx.guild)
        if not player.queue:
            await ctx.reply(
                embed=create_error_embed("Empty Queue", "There are no songs in queue to shuffle."),
                ephemeral=True,
            )
            return

        player.shuffle()
        await ctx.reply(
            embed=create_success_embed("Queue Shuffled", f"🔀 Shuffled **{len(player.queue)}** tracks in queue.")
        )

    @commands.hybrid_command(name="remove", description="Removes a specific song from queue by position number.")
    @app_commands.describe(position="The position number of the song in the queue")
    async def remove_cmd(self, ctx: commands.Context, position: int):
        """Remove a song from queue."""
        player = get_player(self.bot, ctx.guild)
        if not (1 <= position <= len(player.queue)):
            await ctx.reply(
                embed=create_error_embed("Invalid Position", f"Please specify a position between 1 and {len(player.queue)}."),
                ephemeral=True,
            )
            return

        removed = player.queue.pop(position - 1)
        await player.update_setup_panel()
        await ctx.reply(
            embed=create_success_embed("Track Removed", f"🗑️ Removed **{removed.get('title')}** from queue.")
        )

    @commands.hybrid_command(name="clear", description="Clears all upcoming songs from queue.")
    async def clear_cmd(self, ctx: commands.Context):
        """Clear upcoming queue."""
        player = get_player(self.bot, ctx.guild)
        count = len(player.queue)
        player.queue.clear()
        await player.update_setup_panel()
        await ctx.reply(
            embed=create_success_embed("Queue Cleared", f"🧹 Cleared **{count}** songs from queue.")
        )

    @commands.hybrid_command(name="join", aliases=["j", "connect"], description="Connects Gandiva Tunes to your voice channel.")
    async def join_cmd(self, ctx: commands.Context):
        """Connect to voice channel."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.reply(
                embed=create_error_embed("Voice Channel Needed", "You must be connected to a voice channel first."),
                ephemeral=True,
            )
            return

        channel = ctx.author.voice.channel
        player = get_player(self.bot, ctx.guild)

        if ctx.guild.voice_client:
            if ctx.guild.voice_client.channel == channel:
                await ctx.reply(
                    embed=create_error_embed(
                        "Already Connected",
                        f"I am already connected and existed in your voice channel {channel.mention}!",
                    ),
                    ephemeral=True,
                )
                return
            else:
                old_channel = ctx.guild.voice_client.channel
                await ctx.guild.voice_client.move_to(channel)
                player.voice_client = ctx.guild.voice_client
                await ctx.reply(
                    embed=create_success_embed(
                        "Voice Channel Moved",
                        f"Moved from {old_channel.mention} to {channel.mention}!",
                    )
                )
                return

        try:
            player.voice_client = await channel.connect(timeout=20.0, reconnect=True)
            await ctx.reply(
                embed=create_success_embed("Voice Connected", f"Successfully joined {channel.mention}!")
            )
        except Exception as e:
            await ctx.reply(
                embed=create_error_embed("Connection Failed", f"Could not join voice channel: {e}"),
                ephemeral=True,
            )

    @commands.hybrid_command(name="leave", aliases=["dc", "disconnect"], description="Disconnects bot from voice channel.")
    async def leave_cmd(self, ctx: commands.Context):
        """Disconnect bot from voice channel."""
        player = get_player(self.bot, ctx.guild)
        player.stop()
        if ctx.guild.voice_client:
            await ctx.guild.voice_client.disconnect(force=True)
            player.voice_client = None

        await ctx.reply(
            embed=create_success_embed("Disconnected", "Left the voice channel and cleared queue.")
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))
