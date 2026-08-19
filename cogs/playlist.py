"""
Personal Playlist Cog for Gandiva Tunes Discord Music Bot.
Allows users to create, view, add tracks, delete, and play personal cloud playlists.
Credits: Syko Reddy
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from database.db_manager import db_manager
from utils.music_queue import get_player
from utils.music_engine import MusicEngine
from utils.ui_theme import (
    create_success_embed,
    create_error_embed,
    format_duration,
    COLOR_NEON_PURPLE,
    COLOR_NEON_PINK,
    CREDITS_FOOTER,
)


class PlaylistCog(commands.GroupCog, name="playlist"):
    """Manage your personal music playlists."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()

    @app_commands.command(name="create", description="Creates a new personal playlist.")
    @app_commands.describe(name="Name for your new playlist")
    async def create(self, interaction: discord.Interaction, name: str):
        """Create a new playlist."""
        clean_name = name.strip()
        if len(clean_name) > 32:
            await interaction.response.send_message(
                embed=create_error_embed("Name Too Long", "Playlist name must be 32 characters or fewer."),
                ephemeral=True,
            )
            return

        success = await db_manager.create_playlist(interaction.user.id, clean_name)
        if success:
            await interaction.response.send_message(
                embed=create_success_embed(
                    "Playlist Created",
                    f"📁 Playlist **{clean_name}** created!\nAdd songs with `/playlist add {clean_name} <song>`",
                ),
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                embed=create_error_embed("Creation Failed", f"A playlist named `{clean_name}` already exists."),
                ephemeral=True,
            )

    @app_commands.command(name="list", description="Lists all your saved personal playlists.")
    async def list_playlists(self, interaction: discord.Interaction):
        """List all personal playlists."""
        playlists = await db_manager.get_user_playlists(interaction.user.id)
        if not playlists:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "No Playlists",
                    "You haven't created any playlists yet.\nUse `/playlist create <name>` to get started!",
                ),
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title=f"📂 {interaction.user.display_name}'s Playlists",
            color=COLOR_NEON_PURPLE,
        )
        for p in playlists:
            embed.add_field(
                name=f"🎵 {p['name']}",
                value=f"**Tracks:** `{p.get('track_count', 0)}`\n**Created:** `{p.get('created_at', '')[:10]}`",
                inline=True,
            )
        embed.set_footer(text=CREDITS_FOOTER)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="add", description="Adds a song or URL to your personal playlist.")
    @app_commands.describe(
        playlist="Name of your playlist",
        query="Song title, YouTube link, or Spotify link",
    )
    async def add(self, interaction: discord.Interaction, playlist: str, query: str):
        """Add song to playlist."""
        await interaction.response.defer(ephemeral=True)
        
        # Verify playlist exists
        p_record = await db_manager.get_playlist_by_name(interaction.user.id, playlist)
        if not p_record:
            await interaction.followup.send(
                embed=create_error_embed("Not Found", f"Playlist `{playlist}` does not exist."),
                ephemeral=True,
            )
            return

        try:
            tracks = await MusicEngine.extract_info(query, requester=interaction.user)
            if not tracks:
                await interaction.followup.send(
                    embed=create_error_embed("Not Found", f"No tracks found for query: `{query}`."),
                    ephemeral=True,
                )
                return

            added_count = 0
            for t in tracks:
                ok = await db_manager.add_track_to_playlist(
                    user_id=interaction.user.id,
                    playlist_name=playlist,
                    title=t.get("title", "Unknown"),
                    url=t.get("url", ""),
                    duration=t.get("duration", 0),
                    thumbnail=t.get("thumbnail", ""),
                )
                if ok:
                    added_count += 1

            await interaction.followup.send(
                embed=create_success_embed(
                    "Tracks Added",
                    f"✨ Added **{added_count} track(s)** to playlist **{playlist}**!",
                ),
                ephemeral=True,
            )
        except Exception as e:
            await interaction.followup.send(
                embed=create_error_embed("Error Adding Track", str(e)),
                ephemeral=True,
            )

    @app_commands.command(name="view", description="Views the tracks inside a personal playlist.")
    @app_commands.describe(playlist="Name of your playlist", page="Page number")
    async def view_playlist(
        self, interaction: discord.Interaction, playlist: str, page: Optional[int] = 1
    ):
        """View tracks in a playlist."""
        tracks = await db_manager.get_playlist_tracks(interaction.user.id, playlist)
        if not tracks:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Empty Playlist",
                    f"Playlist `{playlist}` is either empty or does not exist.",
                ),
                ephemeral=True,
            )
            return

        per_page = 10
        total_pages = max(1, (len(tracks) + per_page - 1) // per_page)
        page = max(1, min(page or 1, total_pages))

        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, len(tracks))

        embed = discord.Embed(
            title=f"📂 Playlist: {playlist} (Page {page}/{total_pages})",
            color=COLOR_NEON_PINK,
        )
        desc = ""
        for i in range(start_idx, end_idx):
            t = tracks[i]
            dur = format_duration(t.get("duration", 0))
            desc += f"`{i+1}.` [{t['title']}]({t['url']}) `[{dur}]`\n"

        embed.description = desc
        embed.set_footer(
            text=f"Total Songs: {len(tracks)} • Use /playlist play {playlist} to listen • {CREDITS_FOOTER}"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="play", description="Loads and plays all tracks from your personal playlist.")
    @app_commands.describe(playlist="Name of your playlist")
    async def play_playlist(self, interaction: discord.Interaction, playlist: str):
        """Play all tracks from a playlist."""
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message(
                embed=create_error_embed("Voice Required", "You must be in a voice channel to play music."),
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        tracks = await db_manager.get_playlist_tracks(interaction.user.id, playlist)
        if not tracks:
            await interaction.followup.send(
                embed=create_error_embed(
                    "Empty Playlist", f"Playlist `{playlist}` has no songs to play."
                )
            )
            return

        voice_channel = interaction.user.voice.channel
        player = get_player(self.bot, interaction.guild)

        if not interaction.guild.voice_client:
            player.voice_client = await voice_channel.connect(timeout=20.0, reconnect=True)
        elif interaction.guild.voice_client.channel != voice_channel:
            await interaction.guild.voice_client.move_to(voice_channel)
            player.voice_client = interaction.guild.voice_client
        else:
            player.voice_client = interaction.guild.voice_client

        formatted_tracks = [
            {
                "title": t["title"],
                "url": t["url"],
                "stream_url": t["url"],
                "duration": t["duration"],
                "thumbnail": t["thumbnail"],
                "requester": interaction.user,
                "author": "Playlist Track",
            }
            for t in tracks
        ]

        await player.add_tracks(formatted_tracks)
        await interaction.followup.send(
            embed=create_success_embed(
                "Playlist Loaded",
                f"🎧 Loaded **{len(formatted_tracks)} tracks** from playlist **{playlist}** into queue!",
            )
        )

    @app_commands.command(name="remove", description="Removes a specific track from your playlist by track number.")
    @app_commands.describe(
        playlist="Name of your playlist",
        track_number="Track number to remove (from /playlist view)",
    )
    async def remove_track(
        self, interaction: discord.Interaction, playlist: str, track_number: int
    ):
        """Remove a track by index."""
        success = await db_manager.remove_track_from_playlist(
            interaction.user.id, playlist, track_number
        )
        if success:
            await interaction.response.send_message(
                embed=create_success_embed(
                    "Track Removed",
                    f"🗑️ Removed track #{track_number} from playlist **{playlist}**.",
                ),
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Removal Failed",
                    f"Could not remove track #{track_number}. Please check `/playlist view {playlist}`.",
                ),
                ephemeral=True,
            )

    @app_commands.command(name="delete", description="Permanently deletes an entire personal playlist.")
    @app_commands.describe(playlist="Name of your playlist to delete")
    async def delete_playlist(self, interaction: discord.Interaction, playlist: str):
        """Delete an entire playlist."""
        success = await db_manager.delete_playlist(interaction.user.id, playlist)
        if success:
            await interaction.response.send_message(
                embed=create_success_embed(
                    "Playlist Deleted",
                    f"🗑️ Playlist **{playlist}** has been deleted.",
                ),
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                embed=create_error_embed("Delete Failed", f"Playlist `{playlist}` was not found."),
                ephemeral=True,
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(PlaylistCog(bot))
