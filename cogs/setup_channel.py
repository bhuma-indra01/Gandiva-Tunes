"""
Dedicated Music Channel Setup & No-Prefix Song Auto-Player for Gandiva Tunes.
Handles persistent controller panel, No-Prefix server/user permission checks, and auto-deleting message requests.
Credits: Syko Reddy
"""

import discord
from discord.ext import commands
from database.db_manager import db_manager
from utils.music_queue import get_player
from utils.music_engine import MusicEngine
from utils.ui_theme import create_setup_idle_embed, create_success_embed
from utils.views import MusicControlView


class SetupChannelCog(commands.Cog, name="Setup"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="setup",
        description="Creates the dedicated #gandiva-tunes-music channel with persistent interactive controller panel.",
    )
    @commands.has_permissions(manage_channels=True)
    async def setup_channel(self, ctx: commands.Context):
        """Create or configure the dedicated music setup channel."""
        await ctx.defer(ephemeral=True)
        guild = ctx.guild

        # Check if setup channel already exists in DB
        existing_channel_id, _ = await db_manager.get_music_channel(guild.id)
        channel = None
        if existing_channel_id:
            channel = guild.get_channel(existing_channel_id)

        # If channel does not exist, create it
        if not channel:
            channel_name = "gandiva-tunes-music"
            # Look for existing channel with this name
            channel = discord.utils.get(guild.text_channels, name=channel_name)
            if not channel:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(
                        send_messages=True,
                        read_messages=True,
                        embed_links=True,
                        attach_files=True,
                        read_message_history=True,
                    ),
                    guild.me: discord.PermissionOverwrite(
                        send_messages=True,
                        read_messages=True,
                        embed_links=True,
                        manage_messages=True,
                        manage_channels=True,
                    ),
                }
                channel = await guild.create_text_channel(
                    name=channel_name,
                    topic="🏹 Gandiva Tunes Dedicated Controller | Type any song name or link to play! | Credits: Syko Reddy",
                    overwrites=overwrites,
                )

        # Purge existing messages in the channel to ensure a clean slate
        try:
            await channel.purge(limit=50)
        except Exception:
            pass

        # Send persistent idle embed with interactive controller
        player = get_player(self.bot, guild)
        prefix = await db_manager.get_prefix(guild.id)
        idle_embed = create_setup_idle_embed(prefix=prefix)
        view = MusicControlView(player)
        panel_message = await channel.send(embed=idle_embed, view=view)

        # Store in database
        await db_manager.set_music_channel(guild.id, channel.id, panel_message.id)

        await ctx.reply(
            embed=create_success_embed(
                "Music Setup Complete!",
                f"Dedicated music channel is ready at {channel.mention}.\nSimply type any song name or link there to play without prefixes!",
            ),
            ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listen for song queries in the dedicated setup channel, auto-delete, and auto-play."""
        if message.author.bot or not message.guild:
            return

        # Check if message was sent in this guild's dedicated music channel
        channel_id, _ = await db_manager.get_music_channel(message.guild.id)
        if not channel_id or message.channel.id != channel_id:
            return

        # Save query content and delete the user's message immediately
        query = message.content.strip()
        try:
            await message.delete()
        except discord.Forbidden:
            pass
        except Exception:
            pass

        if not query:
            return

        # Check No-Prefix permission:
        # Server Owner and Admins ALWAYS have No-Prefix permission.
        # Other users depend on server-wide No-Prefix toggle or individual user whitelist.
        is_server_owner = message.author.id == message.guild.owner_id
        is_admin = message.author.guild_permissions.administrator
        is_server_on = await db_manager.is_server_noprefix_enabled(message.guild.id)
        is_user_whitelisted = await db_manager.is_user_noprefix_allowed(message.guild.id, message.author.id)

        if not (is_server_owner or is_admin or is_server_on or is_user_whitelisted):
            temp_msg = await message.channel.send(
                f"⚠️ {message.author.mention}, No-Prefix mode is currently disabled for your account. Please use `/play <song>` or ask the Server Owner to enable No-Prefix."
            )
            await temp_msg.delete(delay=6)
            return

        # Check user's voice channel
        if not message.author.voice or not message.author.voice.channel:
            temp_msg = await message.channel.send(
                f"⚠️ {message.author.mention}, you must be connected to a Voice Channel to play music!"
            )
            await temp_msg.delete(delay=5)
            return

        voice_channel = message.author.voice.channel
        player = get_player(self.bot, message.guild)

        # Safe voice connection check
        if not message.guild.voice_client:
            try:
                player.voice_client = await voice_channel.connect(timeout=20.0, reconnect=True)
            except Exception as e:
                temp_msg = await message.channel.send(f"❌ Failed to join voice channel: {e}")
                await temp_msg.delete(delay=5)
                return
        elif message.guild.voice_client.channel != voice_channel:
            try:
                await message.guild.voice_client.move_to(voice_channel)
                player.voice_client = message.guild.voice_client
            except Exception:
                pass
        else:
            player.voice_client = message.guild.voice_client

        # Extract track(s)
        try:
            tracks = await MusicEngine.extract_info(query, requester=message.author)
            if not tracks:
                temp_msg = await message.channel.send(
                    f"❌ {message.author.mention}, no songs found for `{query}`."
                )
                await temp_msg.delete(delay=5)
                return

            if len(tracks) == 1:
                track = tracks[0]
                await player.add_track(track)
                temp_msg = await message.channel.send(
                    f"🎶 **Added to Queue:** `{track.get('title')}` (by {message.author.mention})"
                )
                await temp_msg.delete(delay=5)
            else:
                await player.add_tracks(tracks)
                temp_msg = await message.channel.send(
                    f"📂 **Added {len(tracks)} tracks from playlist** (by {message.author.mention})"
                )
                await temp_msg.delete(delay=5)

        except Exception as e:
            temp_msg = await message.channel.send(
                f"⚠️ Error loading `{query}`: {e}"
            )
            await temp_msg.delete(delay=6)


async def setup(bot: commands.Bot):
    await bot.add_cog(SetupChannelCog(bot))
