"""
Equalizer and Audio Filters Cog for Gandiva Tunes.
Handles real-time audio filters such as Bassboost, 8D audio, Nightcore, and Vaporwave.
Credits: Syko Reddy
"""

import discord
from discord.ext import commands
from discord import app_commands
from typing import Literal
from utils.music_queue import get_player
from utils.ui_theme import create_success_embed, create_error_embed
from utils.views import FilterSelectView


class FiltersCog(commands.Cog, name="Filters"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="filter",
        aliases=["equalizer", "eq"],
        description="Applies audio filters like Bassboost, 8D, Nightcore, and Vaporwave.",
    )
    @app_commands.describe(preset="Choose an audio filter preset")
    async def filter_cmd(
        self,
        ctx: commands.Context,
        preset: Literal[
            "Normal",
            "Bassboost",
            "Extreme Bass",
            "8D",
            "Nightcore",
            "Vaporwave",
            "Pop",
            "Treble",
            "Karaoke",
        ] = "Normal",
    ):
        """Apply audio filter preset."""
        player = get_player(self.bot, ctx.guild)
        if not player.current_track:
            await ctx.reply(
                embed=create_error_embed("No Track Playing", "There is no music playing to apply filters to."),
                ephemeral=True,
            )
            return

        if not ctx.author.voice or (
            ctx.guild.voice_client and ctx.author.voice.channel != ctx.guild.voice_client.channel
        ):
            await ctx.reply(
                embed=create_error_embed("Voice Channel Needed", "You must be in the same voice channel as the bot."),
                ephemeral=True,
            )
            return

        await ctx.defer()
        await player.change_filter(preset)
        await ctx.reply(
            embed=create_success_embed(
                "Filter Applied",
                f"⚡ Audio filter set to **{preset}**!\nRe-processing stream with FFmpeg equalizers...",
            )
        )

    @commands.hybrid_command(name="equalizer_menu", description="Opens interactive visual equalizer menu.")
    async def eq_menu(self, ctx: commands.Context):
        """Show interactive filter menu."""
        player = get_player(self.bot, ctx.guild)
        view = FilterSelectView(player)
        await ctx.reply("🎚️ **Select an Audio Filter Preset below:**", view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(FiltersCog(bot))
