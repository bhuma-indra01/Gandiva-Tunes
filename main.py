"""
Gandiva Tunes - All-In-One Discord Music Bot
Created & Developed by: Syko Reddy

Features:
- Dedicated #gandiva-tunes-music Setup Channel with No-Prefix Auto-Play & Auto-Delete
- Persistent Interactive Controller Panel with Live Progress Timing
- Personal Cloud Playlists (SQLite)
- 24/7 Voice Channel Stay Mode
- Equalizer & Audio Filters (Bassboost, 8D, Nightcore, Vaporwave, etc.)
- Owner Avatar & Banner Changer (with animated GIF support)
- Production Ready for BOTH Railway.app & Render.com Deployments
"""

import sys
import os
import asyncio
import logging
import discord
from discord.ext import commands
from colorama import init, Fore, Style

from config import (
    DISCORD_TOKEN,
    DEFAULT_PREFIX,
    BOT_NAME,
    CREDITS_TEXT,
    CREDITS_FOOTER,
)
from database.db_manager import db_manager
from utils.music_queue import get_player, cleanup_player
from keep_alive import start_keep_alive

# Initialize terminal colors
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("GandivaTunes")


async def get_prefix(bot: commands.Bot, message: discord.Message) -> list[str]:
    """Retrieve dynamic prefix per guild or default prefix."""
    if not message.guild:
        return [DEFAULT_PREFIX]
    custom_prefix = await db_manager.get_prefix(message.guild.id)
    return commands.when_mentioned_or(custom_prefix, DEFAULT_PREFIX)(bot, message)


class GandivaBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.voice_states = True
        intents.members = True

        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            help_command=None,
            case_insensitive=True,
        )

    async def setup_hook(self):
        """Initialize database, start keep-alive web server, load extensions, and sync commands."""
        # Start Keep-Alive web server for Render / Uptime monitoring
        try:
            await start_keep_alive()
        except Exception as e:
            logger.warning(f"Could not start keep_alive web server: {e}")

        logger.info("Initializing SQLite database...")
        await db_manager.init_db()

        # Load Cogs
        initial_extensions = [
            "cogs.music",
            "cogs.setup_channel",
            "cogs.playlist",
            "cogs.filters",
            "cogs.owner",
            "cogs.general",
            "cogs.noprefix",
        ]

        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")

        # Sync Slash Commands globally
        try:
            logger.info("Syncing Slash Commands globally...")
            synced = await self.tree.sync()
            logger.info(f"Successfully synced {len(synced)} Slash Commands.")
        except Exception as e:
            logger.error(f"Failed to sync Slash Commands: {e}")

    async def on_ready(self):
        """Triggered when bot connects to Discord."""
        banner = f"""
{Fore.CYAN}=============================================================
{Fore.MAGENTA}   🏹  G A N D I V A   T U N E S  🏹
{Fore.CYAN}   Pure Sound, Epic Beats • All-In-One Discord Music Bot
{Fore.YELLOW}   Credits & Developer: {CREDITS_TEXT}
{Fore.CYAN}=============================================================
{Fore.GREEN}[✓] Logged in as : {self.user.name}#{self.user.discriminator} (ID: {self.user.id})
{Fore.GREEN}[✓] Connected to : {len(self.guilds)} server(s)
{Fore.GREEN}[✓] Discord.py   : v{discord.__version__}
{Fore.GREEN}[✓] Deploy Target: Railway.app & Render.com
{Fore.CYAN}=============================================================
{Style.RESET_ALL}"""
        print(banner)

        # Set presence
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name=f"/play | {BOT_NAME} 🏹",
        )
        await self.change_presence(status=discord.Status.online, activity=activity)

    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        """Handle voice channel disconnects, member departures, and 24/7 mode."""
        # If bot itself was disconnected
        if member.id == self.user.id:
            if before.channel and not after.channel:
                cleanup_player(before.channel.guild.id)
            return

        # If a user leaves the bot's voice channel
        if before.channel and self.user in before.channel.members:
            # Check remaining non-bot members
            non_bots = [m for m in before.channel.members if not m.bot]
            if len(non_bots) == 0:
                is_247 = await db_manager.get_247(before.channel.guild.id)
                if not is_247:
                    player = get_player(self, before.channel.guild)
                    player._start_idle_timer()


def main():
    """Main execution function."""
    if not DISCORD_TOKEN or DISCORD_TOKEN == "your_bot_token_here":
        print(
            f"{Fore.RED}[!] ERROR: DISCORD_TOKEN is not set in your .env file or host environment variables!\n"
            f"Please provide your Discord Bot Token to run Gandiva Tunes.\n"
            f"Get one from: https://discord.com/developers/applications{Style.RESET_ALL}"
        )
        sys.exit(1)

    bot = GandivaBot()
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
