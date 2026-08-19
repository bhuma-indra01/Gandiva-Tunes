"""
General & Utility Commands Cog for Gandiva Tunes Discord Music Bot.
Includes /credits, /help, /247, /ping, /stats, and /prefix commands.
Credits: Syko Reddy
"""

import time
import platform
import discord
from discord.ext import commands
from discord import app_commands
from database.db_manager import db_manager
from utils.music_queue import get_player
from utils.ui_theme import (
    create_credits_embed,
    create_success_embed,
    create_error_embed,
    COLOR_NEON_CYAN,
    CREDITS_FOOTER,
    BOT_NAME,
)

START_TIME = time.time()


class GeneralCog(commands.Cog, name="General"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="credits",
        aliases=["developer", "author"],
        description="Displays the official credits and developer showcase.",
    )
    async def credits_cmd(self, ctx: commands.Context):
        """Show bot author and credits."""
        embed = create_credits_embed()
        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="247",
        aliases=["twentyfourseven", "stay"],
        description="Toggles 24/7 voice channel stay mode for this server.",
    )
    @commands.has_permissions(manage_guild=True)
    async def toggle_247(self, ctx: commands.Context):
        """Toggle 24/7 mode."""
        current_status = await db_manager.get_247(ctx.guild.id)
        new_status = not current_status
        await db_manager.set_247(ctx.guild.id, new_status)

        player = get_player(self.bot, ctx.guild)
        player.is_247 = new_status
        await player.update_setup_panel()

        if new_status:
            await ctx.reply(
                embed=create_success_embed(
                    "24/7 Mode Enabled",
                    "🟢 **Gandiva Tunes will now stay in voice channel 24/7** even when idle!",
                )
            )
        else:
            await ctx.reply(
                embed=create_success_embed(
                    "24/7 Mode Disabled",
                    "⚪ **24/7 Mode disabled.** The bot will leave after idle timeout.",
                )
            )

    @commands.hybrid_command(
        name="prefix",
        description="Changes the bot command prefix for this server.",
    )
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(new_prefix="New prefix symbol (e.g. !, ?, $)")
    async def change_prefix(self, ctx: commands.Context, new_prefix: str):
        """Change prefix."""
        clean_prefix = new_prefix.strip()
        if len(clean_prefix) > 5:
            await ctx.reply(
                embed=create_error_embed("Prefix Too Long", "Prefix cannot exceed 5 characters."),
                ephemeral=True,
            )
            return

        await db_manager.set_prefix(ctx.guild.id, clean_prefix)
        await ctx.reply(
            embed=create_success_embed(
                "Prefix Updated",
                f"Prefix changed to `{clean_prefix}`. Example: `{clean_prefix}play song`",
            )
        )

    @commands.hybrid_command(
        name="ping",
        description="Checks the bot latency and responsiveness.",
    )
    async def ping_cmd(self, ctx: commands.Context):
        """Show latency."""
        start_time = time.monotonic()
        msg = await ctx.reply("📡 Calculating ping...")
        end_time = time.monotonic()
        
        api_latency = round((end_time - start_time) * 1000)
        ws_latency = round(self.bot.latency * 1000)

        embed = discord.Embed(
            title=f"🏹 {BOT_NAME} • Latency",
            color=COLOR_NEON_CYAN,
        )
        embed.add_field(name="🌐 WebSocket Latency", value=f"`{ws_latency} ms`", inline=True)
        embed.add_field(name="⚡ REST API Latency", value=f"`{api_latency} ms`", inline=True)
        embed.set_footer(text=CREDITS_FOOTER)
        await msg.edit(content=None, embed=embed)

    @commands.hybrid_command(
        name="stats",
        description="Shows bot statistics, server count, and runtime details.",
    )
    async def stats_cmd(self, ctx: commands.Context):
        """Show bot stats."""
        uptime_seconds = int(time.time() - START_TIME)
        hours = uptime_seconds // 3600
        mins = (uptime_seconds % 3600) // 60
        secs = uptime_seconds % 60
        uptime_str = f"{hours}h {mins}m {secs}s"

        total_guilds = len(self.bot.guilds)
        total_users = sum(g.member_count or 0 for g in self.bot.guilds)

        embed = discord.Embed(
            title=f"📊 {BOT_NAME} • Live Statistics",
            color=COLOR_NEON_CYAN,
        )
        embed.add_field(name="🏰 Servers", value=f"`{total_guilds}`", inline=True)
        embed.add_field(name="👥 Total Users", value=f"`{total_users:,}`", inline=True)
        embed.add_field(name="⏱️ Bot Uptime", value=f"`{uptime_str}`", inline=True)
        embed.add_field(name="🐍 Python Version", value=f"`{platform.python_version()}`", inline=True)
        embed.add_field(name="📦 Discord.py", value=f"`v{discord.__version__}`", inline=True)
        embed.add_field(name="👑 Developer", value="`Syko Reddy`", inline=True)
        embed.set_footer(text=CREDITS_FOOTER)
        await ctx.reply(embed=embed)

    @commands.hybrid_command(
        name="help",
        description="Displays the interactive help guide and command list.",
    )
    async def help_cmd(self, ctx: commands.Context):
        """Show full help menu."""
        prefix = await db_manager.get_prefix(ctx.guild.id) if ctx.guild else "!"

        embed = discord.Embed(
            title=f"🏹 {BOT_NAME} • Commands Guide",
            description=(
                f"**Developer Credits:** `Syko Reddy`\n"
                f"**Current Server Prefix:** `{prefix}` or use `/` Slash Commands\n\n"
                f"### 🎛️ **Setup & Configuration**\n"
                f"• `/setup` - Creates dedicated `#gandiva-tunes-music` channel with interactive panel.\n"
                f"• `/247` - Toggles 24/7 voice channel stay mode.\n"
                f"• `/prefix <symbol>` - Change prefix for this server.\n"
                f"• `/noprefix server <enable/disable>` - [Server Owner] Toggle No-Prefix server-wide.\n"
                f"• `/noprefix user <add/remove> <user>` - [Server Owner] Whitelist specific users for No-Prefix.\n"
                f"• `/noprefix list` - View whitelisted No-Prefix users.\n\n"
                f"### 🎵 **Music Playback**\n"
                f"• `/play <query/url>` - Play YouTube, Spotify, SoundCloud tracks or playlists.\n"
                f"• `/pause` / `/resume` - Pause or unpause audio.\n"
                f"• `/skip` - Skip to next song.\n"
                f"• `/stop` - Stop playback and clear queue.\n"
                f"• `/queue` - View upcoming songs with interactive pagination.\n"
                f"• `/nowplaying` - View current track with live progress timing.\n"
                f"• `/volume <0-150>` - Change playback volume.\n"
                f"• `/loop <off|track|queue>` - Change loop mode.\n"
                f"• `/shuffle` - Randomize queue order.\n"
                f"• `/filter <preset>` - Apply Bassboost, 8D, Nightcore, Vaporwave, etc.\n\n"
                f"### 📂 **Personal Cloud Playlists**\n"
                f"• `/playlist create <name>` - Create a private playlist.\n"
                f"• `/playlist add <name> <song>` - Add song to your playlist.\n"
                f"• `/playlist play <name>` - Load and play your playlist.\n"
                f"• `/playlist list` - View all your playlists.\n"
                f"• `/playlist view <name>` - View tracks in a playlist.\n"
                f"• `/playlist delete <name>` - Delete a playlist.\n\n"
                f"### 👑 **Bot Owner Only**\n"
                f"• `/setavatar <url/attachment>` - Update bot avatar (supports GIFs).\n"
                f"• `/setbanner <url/attachment>` - Update bot banner (supports GIFs).\n"
                f"• `/setname <name>` - Update bot username.\n"
                f"• `/setstatus <type> <text>` - Update activity status.\n"
                f"• `/sync` - Sync slash commands globally.\n"
            ),
            color=COLOR_NEON_CYAN,
        )
        embed.set_footer(text=CREDITS_FOOTER)
        await ctx.reply(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(GeneralCog(bot))
