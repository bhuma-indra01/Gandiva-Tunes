"""
Interactive Discord Views, Buttons, Select Menus, and Modals for Gandiva Tunes.
Neon Glassmorphic styled controls for music playback and playlist management.
Credits: Syko Reddy
"""

import discord
from typing import TYPE_CHECKING, Optional, List
from database.db_manager import db_manager
from utils.ui_theme import (
    create_queue_embed,
    create_success_embed,
    create_error_embed,
    create_now_playing_embed,
)
from utils.music_engine import AUDIO_FILTERS

if TYPE_CHECKING:
    from utils.music_queue import GuildPlayer


class MusicControlView(discord.ui.View):
    """Persistent interactive controller view for music playback."""

    def __init__(self, player: "GuildPlayer"):
        super().__init__(timeout=None)
        self.player = player

    async def _check_user_voice(self, interaction: discord.Interaction) -> bool:
        """Verify user is in the same voice channel as the bot."""
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Voice Channel Required",
                    "You must be connected to a voice channel to use music controls.",
                ),
                ephemeral=True,
            )
            return False

        if (
            interaction.guild.voice_client
            and interaction.user.voice.channel != interaction.guild.voice_client.channel
        ):
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Wrong Voice Channel",
                    f"You must be in {interaction.guild.voice_client.channel.mention} to control music.",
                ),
                ephemeral=True,
            )
            return False

        return True

    # Row 0: Play/Pause, Skip, Stop, Loop, Shuffle
    @discord.ui.button(
        emoji="⏯️", style=discord.ButtonStyle.primary, custom_id="gandiva_play_pause", row=0
    )
    async def play_pause_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_user_voice(interaction):
            return

        if self.player.is_paused:
            self.player.resume()
            await interaction.response.send_message("▶️ Resumed playback.", ephemeral=True)
        elif self.player.is_playing:
            self.player.pause()
            await interaction.response.send_message("⏸️ Paused playback.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No track currently playing.", ephemeral=True)

    @discord.ui.button(
        emoji="⏭️", style=discord.ButtonStyle.secondary, custom_id="gandiva_skip", row=0
    )
    async def skip_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_user_voice(interaction):
            return

        if self.player.is_playing or self.player.is_paused:
            self.player.skip()
            await interaction.response.send_message("⏭️ Skipped current track.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Nothing to skip.", ephemeral=True)

    @discord.ui.button(
        emoji="⏹️", style=discord.ButtonStyle.danger, custom_id="gandiva_stop", row=0
    )
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_user_voice(interaction):
            return

        self.player.stop()
        await interaction.response.send_message("⏹️ Music stopped and queue cleared.", ephemeral=True)

    @discord.ui.button(
        emoji="🔁", style=discord.ButtonStyle.secondary, custom_id="gandiva_loop", row=0
    )
    async def loop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_user_voice(interaction):
            return

        new_mode = self.player.toggle_loop()
        mode_names = {"OFF": "Loop Disabled", "TRACK": "Loop Single Track", "QUEUE": "Loop Entire Queue"}
        await interaction.response.send_message(
            f"🔁 Loop mode set to: **{mode_names.get(new_mode, new_mode)}**", ephemeral=True
        )

    @discord.ui.button(
        emoji="🔀", style=discord.ButtonStyle.secondary, custom_id="gandiva_shuffle", row=0
    )
    async def shuffle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_user_voice(interaction):
            return

        if not self.player.queue:
            await interaction.response.send_message("❌ Queue is empty, nothing to shuffle.", ephemeral=True)
            return

        self.player.shuffle()
        await interaction.response.send_message("🔀 Queue shuffled successfully!", ephemeral=True)

    # Row 1: Volume Down, Volume Up, Queue, Filters, Add to Playlist
    @discord.ui.button(
        emoji="🔉", style=discord.ButtonStyle.secondary, custom_id="gandiva_voldown", row=1
    )
    async def volume_down_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_user_voice(interaction):
            return

        new_vol = max(0, self.player.volume - 10)
        self.player.set_volume(new_vol)
        await interaction.response.send_message(f"🔉 Volume reduced to **{new_vol}%**", ephemeral=True)

    @discord.ui.button(
        emoji="🔊", style=discord.ButtonStyle.secondary, custom_id="gandiva_volup", row=1
    )
    async def volume_up_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_user_voice(interaction):
            return

        new_vol = min(150, self.player.volume + 10)
        self.player.set_volume(new_vol)
        await interaction.response.send_message(f"🔊 Volume increased to **{new_vol}%**", ephemeral=True)

    @discord.ui.button(
        emoji="📜", label="Queue", style=discord.ButtonStyle.primary, custom_id="gandiva_queue", row=1
    )
    async def queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = create_queue_embed(
            queue_list=self.player.queue,
            current_track=self.player.current_track,
            page=1,
            per_page=10,
        )
        view = QueuePaginationView(self.player, current_page=1)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @discord.ui.button(
        emoji="⚡", label="Equalizer", style=discord.ButtonStyle.secondary, custom_id="gandiva_filters", row=1
    )
    async def filters_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_user_voice(interaction):
            return

        view = FilterSelectView(self.player)
        await interaction.response.send_message(
            "🎚️ **Select an Equalizer / Audio Filter preset:**", view=view, ephemeral=True
        )

    @discord.ui.button(
        emoji="⭐", label="Save Track", style=discord.ButtonStyle.success, custom_id="gandiva_fav", row=1
    )
    async def save_track_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.player.current_track:
            await interaction.response.send_message("❌ No track currently playing to save.", ephemeral=True)
            return

        playlists = await db_manager.get_user_playlists(interaction.user.id)
        if not playlists:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "No Playlists Found",
                    "You don't have any personal playlists yet!\nCreate one using `/playlist create <name>`",
                ),
                ephemeral=True,
            )
            return

        view = AddToPlaylistSelectView(self.player.current_track, playlists)
        await interaction.response.send_message(
            "⭐ **Select a personal playlist to save this track:**", view=view, ephemeral=True
        )


class FilterSelectView(discord.ui.View):
    """Dropdown menu for selecting audio filters."""

    def __init__(self, player: "GuildPlayer"):
        super().__init__(timeout=60)
        self.player = player

        options = [
            discord.SelectOption(label="Normal (Reset)", value="Normal", description="Default clean audio output", emoji="🎵"),
            discord.SelectOption(label="Bassboost", value="Bassboost", description="Deep rich enhanced bass", emoji="🔊"),
            discord.SelectOption(label="Extreme Bass", value="Extreme Bass", description="Maximum heavy bass rumble", emoji="💥"),
            discord.SelectOption(label="8D Audio", value="8D", description="Pulsating 360-degree spatial surround sound", emoji="🎧"),
            discord.SelectOption(label="Nightcore", value="Nightcore", description="High-pitch fast tempo beats", emoji="🌙"),
            discord.SelectOption(label="Vaporwave", value="Vaporwave", description="Slow-tempo retro aesthetic vibe", emoji="🌊"),
            discord.SelectOption(label="Pop", value="Pop", description="Crisp vocal and midrange boost", emoji="🎤"),
            discord.SelectOption(label="Treble", value="Treble", description="Enhanced high frequencies", emoji="✨"),
            discord.SelectOption(label="Karaoke", value="Karaoke", description="Reduces center vocal channel", emoji="🎙️"),
        ]

        select = discord.ui.Select(
            placeholder="Choose an audio filter preset...",
            min_values=1,
            max_values=1,
            options=options,
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        selected_filter = interaction.data["values"][0]
        await self.player.change_filter(selected_filter)
        await interaction.response.send_message(
            f"⚡ Audio filter set to **{selected_filter}**! Reloading audio stream...",
            ephemeral=True,
        )


class QueuePaginationView(discord.ui.View):
    """Pagination view for navigating the queue."""

    def __init__(self, player: "GuildPlayer", current_page: int = 1):
        super().__init__(timeout=120)
        self.player = player
        self.current_page = current_page
        self.per_page = 10

    def _get_total_pages(self) -> int:
        return max(1, (len(self.player.queue) + self.per_page - 1) // self.per_page)

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        total_pages = self._get_total_pages()
        if self.current_page > 1:
            self.current_page -= 1
        else:
            self.current_page = total_pages

        embed = create_queue_embed(
            queue_list=self.player.queue,
            current_track=self.player.current_track,
            page=self.current_page,
            per_page=self.per_page,
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        total_pages = self._get_total_pages()
        if self.current_page < total_pages:
            self.current_page += 1
        else:
            self.current_page = 1

        embed = create_queue_embed(
            queue_list=self.player.queue,
            current_track=self.player.current_track,
            page=self.current_page,
            per_page=self.per_page,
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(emoji="🔄", label="Refresh", style=discord.ButtonStyle.primary)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = create_queue_embed(
            queue_list=self.player.queue,
            current_track=self.player.current_track,
            page=self.current_page,
            per_page=self.per_page,
        )
        await interaction.response.edit_message(embed=embed, view=self)


class AddToPlaylistSelectView(discord.ui.View):
    """Dropdown view to choose which personal playlist to save a track to."""

    def __init__(self, track: dict, playlists: List[dict]):
        super().__init__(timeout=60)
        self.track = track

        options = [
            discord.SelectOption(
                label=p["name"][:100],
                value=p["name"],
                description=f"Total tracks: {p.get('track_count', 0)}",
                emoji="📂",
            )
            for p in playlists[:25]
        ]

        select = discord.ui.Select(
            placeholder="Select destination playlist...",
            min_values=1,
            max_values=1,
            options=options,
        )
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        playlist_name = interaction.data["values"][0]
        success = await db_manager.add_track_to_playlist(
            user_id=interaction.user.id,
            playlist_name=playlist_name,
            title=self.track.get("title", "Unknown Track"),
            url=self.track.get("url", ""),
            duration=self.track.get("duration", 0),
            thumbnail=self.track.get("thumbnail", ""),
        )
        if success:
            await interaction.response.send_message(
                embed=create_success_embed(
                    "Track Saved",
                    f"Saved **{self.track.get('title')}** to your playlist **{playlist_name}**!",
                ),
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                embed=create_error_embed("Failed to Save", "Could not save track to playlist."),
                ephemeral=True,
            )
