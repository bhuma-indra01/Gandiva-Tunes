"""
No-Prefix Management Cog for Gandiva Tunes.
Allows Server Owners to enable/disable No-Prefix mode server-wide and grant/revoke access for specific users.
Credits: Syko Reddy
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Literal
from database.db_manager import db_manager
from utils.ui_theme import create_success_embed, create_error_embed, COLOR_NEON_CYAN, CREDITS_FOOTER


class NoPrefixCog(commands.GroupCog, name="noprefix"):
    """Manage No-Prefix mode for the server and individual users."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        super().__init__()

    async def _check_server_owner_or_admin(self, interaction: discord.Interaction) -> bool:
        """Verify user is Server Owner or has Administrator permission."""
        if interaction.guild and (
            interaction.user.id == interaction.guild.owner_id
            or interaction.user.guild_permissions.administrator
        ):
            return True
        await interaction.response.send_message(
            embed=create_error_embed(
                "Access Denied",
                "Only the **Server Owner** or **Administrators** can manage No-Prefix settings.",
            ),
            ephemeral=True,
        )
        return False

    @app_commands.command(
        name="server",
        description="[SERVER OWNER/ADMIN] Turn No-Prefix mode ON or OFF for the entire server.",
    )
    @app_commands.describe(status="Choose to enable or disable No-Prefix server-wide")
    async def toggle_server_noprefix(
        self, interaction: discord.Interaction, status: Literal["enable", "disable"]
    ):
        """Toggle No-Prefix server-wide."""
        if not await self._check_server_owner_or_admin(interaction):
            return

        is_enabled = status == "enable"
        await db_manager.set_server_noprefix(interaction.guild.id, is_enabled)

        if is_enabled:
            await interaction.response.send_message(
                embed=create_success_embed(
                    "No-Prefix Enabled",
                    "🟢 **No-Prefix mode is now ENABLED for this server!**\nUsers can request songs without prefixes in the music channel.",
                )
            )
        else:
            await interaction.response.send_message(
                embed=create_success_embed(
                    "No-Prefix Disabled",
                    "⚪ **No-Prefix mode is now DISABLED for this server.**\nUsers must use prefix or slash commands.",
                )
            )

    @app_commands.command(
        name="user",
        description="[SERVER OWNER/ADMIN] Grant or revoke No-Prefix permission for a specific user.",
    )
    @app_commands.describe(
        action="Choose to add or remove user",
        user="The server member to configure",
    )
    async def manage_user_noprefix(
        self,
        interaction: discord.Interaction,
        action: Literal["add", "remove"],
        user: discord.Member,
    ):
        """Add or remove user from No-Prefix whitelist."""
        if not await self._check_server_owner_or_admin(interaction):
            return

        if action == "add":
            ok = await db_manager.add_user_noprefix(interaction.guild.id, user.id)
            if ok:
                await interaction.response.send_message(
                    embed=create_success_embed(
                        "User Granted No-Prefix",
                        f"✨ Granted No-Prefix permission to {user.mention}!",
                    )
                )
            else:
                await interaction.response.send_message(
                    embed=create_error_embed(
                        "Already Exists", f"{user.mention} already has No-Prefix permission."
                    ),
                    ephemeral=True,
                )
        else:
            ok = await db_manager.remove_user_noprefix(interaction.guild.id, user.id)
            if ok:
                await interaction.response.send_message(
                    embed=create_success_embed(
                        "User Revoked No-Prefix",
                        f"🗑️ Removed No-Prefix permission from {user.mention}.",
                    )
                )
            else:
                await interaction.response.send_message(
                    embed=create_error_embed(
                        "Not Found", f"{user.mention} did not have No-Prefix permission."
                    ),
                    ephemeral=True,
                )

    @app_commands.command(name="list", description="Lists all users who have No-Prefix permission.")
    async def list_noprefix(self, interaction: discord.Interaction):
        """List whitelisted No-Prefix users."""
        user_ids = await db_manager.get_user_noprefix_list(interaction.guild.id)
        is_server_on = await db_manager.is_server_noprefix_enabled(interaction.guild.id)

        server_status_str = "🟢 Enabled (All users in music zone)" if is_server_on else "⚪ Disabled (Whitelist only)"

        embed = discord.Embed(
            title=f"🏹 {interaction.guild.name} • No-Prefix Settings",
            color=COLOR_NEON_CYAN,
        )
        embed.add_field(name="🌐 Server Status", value=server_status_str, inline=False)

        if not user_ids:
            embed.add_field(
                name="👥 Whitelisted Users",
                value="_No individual users added yet. Server Owner can add users using `/noprefix user add <user>`._",
                inline=False,
            )
        else:
            user_mentions = [f"<@{uid}>" for uid in user_ids]
            embed.add_field(
                name=f"👥 Whitelisted Users ({len(user_ids)})",
                value=", ".join(user_mentions),
                inline=False,
            )

        embed.set_footer(text=CREDITS_FOOTER)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(NoPrefixCog(bot))
