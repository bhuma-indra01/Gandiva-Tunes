"""
Bot Owner Management Cog for Gandiva Tunes.
Provides owner-exclusive commands for updating bot avatar (GIF / static),
banner (GIF / static), username, status, and syncing slash commands.
Credits: Syko Reddy
"""

import discord
import aiohttp
from discord.ext import commands
from discord import app_commands
from typing import Optional, Literal
from config import OWNER_ID, BOT_NAME, CREDITS_FOOTER
from utils.ui_theme import create_success_embed, create_error_embed


class OwnerCog(commands.Cog, name="Owner"):
    """Owner only administrative commands."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _is_owner_check(self, user: discord.User) -> bool:
        """Verify if user is the designated owner or app owner."""
        if OWNER_ID and user.id == OWNER_ID:
            return True
        return await self.bot.is_owner(user)

    async def _download_bytes(self, url: str) -> bytes:
        """Download binary data from URL."""
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                if resp.status == 200:
                    return await resp.read()
                raise Exception(f"HTTP request failed with status code {resp.status}")

    # ----------------- AVATAR CHANGER -----------------
    @commands.hybrid_command(
        name="setavatar",
        description="[OWNER ONLY] Changes bot avatar using an image/GIF URL or file attachment.",
    )
    @app_commands.describe(
        url="Direct URL to image or animated GIF",
        attachment="Upload image or animated GIF file",
    )
    async def set_avatar(
        self,
        ctx: commands.Context,
        url: Optional[str] = None,
        attachment: Optional[discord.Attachment] = None,
    ):
        """Set bot avatar (supports animated GIFs)."""
        if not await self._is_owner_check(ctx.author):
            await ctx.reply(
                embed=create_error_embed("Access Denied", "Only the Bot Owner (`Syko Reddy`) can run this command."),
                ephemeral=True,
            )
            return

        target_url = None
        if attachment:
            target_url = attachment.url
        elif url:
            target_url = url
        elif ctx.message.attachments:
            target_url = ctx.message.attachments[0].url

        if not target_url:
            await ctx.reply(
                embed=create_error_embed(
                    "Missing Image", "Please provide a valid image/GIF URL or upload a file attachment."
                ),
                ephemeral=True,
            )
            return

        await ctx.defer(ephemeral=True)
        try:
            image_bytes = await self._download_bytes(target_url)
            await self.bot.user.edit(avatar=image_bytes)
            await ctx.reply(
                embed=create_success_embed(
                    "Avatar Updated!",
                    f"✨ Bot avatar successfully updated (supports animated GIFs & images)!\n[View New Avatar]({target_url})",
                ),
                ephemeral=True,
            )
        except discord.HTTPException as e:
            await ctx.reply(
                embed=create_error_embed(
                    "Discord API Rate-Limit / Error",
                    f"Could not change avatar. Discord allows avatar changes twice every 10 minutes.\nError: `{e}`",
                ),
                ephemeral=True,
            )
        except Exception as e:
            await ctx.reply(
                embed=create_error_embed("Failed to Update Avatar", str(e)),
                ephemeral=True,
            )

    # ----------------- BANNER CHANGER -----------------
    @commands.hybrid_command(
        name="setbanner",
        description="[OWNER ONLY] Changes bot profile banner using an image/GIF URL or file attachment.",
    )
    @app_commands.describe(
        url="Direct URL to image or animated GIF",
        attachment="Upload image or animated GIF file",
    )
    async def set_banner(
        self,
        ctx: commands.Context,
        url: Optional[str] = None,
        attachment: Optional[discord.Attachment] = None,
    ):
        """Set bot banner (supports animated GIFs)."""
        if not await self._is_owner_check(ctx.author):
            await ctx.reply(
                embed=create_error_embed("Access Denied", "Only the Bot Owner can run this command."),
                ephemeral=True,
            )
            return

        target_url = None
        if attachment:
            target_url = attachment.url
        elif url:
            target_url = url
        elif ctx.message.attachments:
            target_url = ctx.message.attachments[0].url

        if not target_url:
            await ctx.reply(
                embed=create_error_embed(
                    "Missing Image", "Please provide a valid banner image/GIF URL or upload a file attachment."
                ),
                ephemeral=True,
            )
            return

        await ctx.defer(ephemeral=True)
        try:
            image_bytes = await self._download_bytes(target_url)
            await self.bot.user.edit(banner=image_bytes)
            await ctx.reply(
                embed=create_success_embed(
                    "Banner Updated!",
                    f"✨ Bot banner successfully updated!\n[View New Banner]({target_url})",
                ),
                ephemeral=True,
            )
        except discord.HTTPException as e:
            await ctx.reply(
                embed=create_error_embed(
                    "Discord API Error",
                    f"Could not change banner. (Note: Bot account must meet Discord developer banner requirements).\nError: `{e}`",
                ),
                ephemeral=True,
            )
        except Exception as e:
            await ctx.reply(
                embed=create_error_embed("Failed to Update Banner", str(e)),
                ephemeral=True,
            )

    # ----------------- USERNAME CHANGER -----------------
    @commands.hybrid_command(
        name="setname",
        description="[OWNER ONLY] Changes the bot username.",
    )
    @app_commands.describe(new_name="The new username for the bot")
    async def set_name(self, ctx: commands.Context, *, new_name: str):
        """Change bot username."""
        if not await self._is_owner_check(ctx.author):
            await ctx.reply(
                embed=create_error_embed("Access Denied", "Only the Bot Owner can run this command."),
                ephemeral=True,
            )
            return

        clean_name = new_name.strip()
        if len(clean_name) < 2 or len(clean_name) > 32:
            await ctx.reply(
                embed=create_error_embed("Invalid Name", "Bot username must be between 2 and 32 characters."),
                ephemeral=True,
            )
            return

        await ctx.defer(ephemeral=True)
        try:
            await self.bot.user.edit(username=clean_name)
            await ctx.reply(
                embed=create_success_embed(
                    "Username Updated!", f"Bot username changed to **{clean_name}**."
                ),
                ephemeral=True,
            )
        except Exception as e:
            await ctx.reply(
                embed=create_error_embed("Failed to Update Username", str(e)),
                ephemeral=True,
            )

    # ----------------- STATUS & ACTIVITY -----------------
    @commands.hybrid_command(
        name="setstatus",
        description="[OWNER ONLY] Changes the bot activity status text and type.",
    )
    @app_commands.describe(
        activity_type="Type of activity (playing, listening, watching, streaming)",
        status_text="Text to display in status",
    )
    async def set_status(
        self,
        ctx: commands.Context,
        activity_type: Literal["listening", "playing", "watching", "streaming"],
        *,
        status_text: str,
    ):
        """Change bot presence activity."""
        if not await self._is_owner_check(ctx.author):
            await ctx.reply(
                embed=create_error_embed("Access Denied", "Only the Bot Owner can run this command."),
                ephemeral=True,
            )
            return

        activity_map = {
            "listening": discord.ActivityType.listening,
            "playing": discord.ActivityType.playing,
            "watching": discord.ActivityType.watching,
            "streaming": discord.ActivityType.streaming,
        }

        act_type = activity_map.get(activity_type, discord.ActivityType.listening)
        activity = discord.Activity(type=act_type, name=status_text)
        await self.bot.change_presence(activity=activity)

        await ctx.reply(
            embed=create_success_embed(
                "Status Updated",
                f"Bot presence updated to: **{activity_type.capitalize()} {status_text}**",
            ),
            ephemeral=True,
        )

    # ----------------- SLASH COMMANDS SYNC -----------------
    @commands.hybrid_command(
        name="sync",
        description="[OWNER ONLY] Forces synchronization of Slash Commands with Discord.",
    )
    async def sync_tree(self, ctx: commands.Context):
        """Sync application command tree globally."""
        if not await self._is_owner_check(ctx.author):
            await ctx.reply(
                embed=create_error_embed("Access Denied", "Only the Bot Owner can run this command."),
                ephemeral=True,
            )
            return

        await ctx.defer(ephemeral=True)
        synced = await self.bot.tree.sync()
        await ctx.reply(
            embed=create_success_embed(
                "Tree Synchronized",
                f"Successfully synced **{len(synced)} Slash Commands** globally with Discord API!",
            ),
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(OwnerCog(bot))
