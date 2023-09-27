import logging

import discord
from discord import app_commands as apc
from discord.ext import commands

from bot import Bot

_log = logging.getLogger(__name__)


class Event(commands.Cog):
    """Events for handling listeners and startup."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.bot.tree.error(self.on_app_command_error)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        _log.info("Logged in as %s (User ID: %d).", self.bot.user, self.bot.user.id)

        before_commands = self.bot.tree.get_commands()
        after_commands = await self.bot.tree.sync()

        _log.info(
            "Successfully synced %d/%d commands.",
            len(after_commands),
            len(before_commands),
        )

        activity = discord.Activity(type=discord.ActivityType.watching, name=".gg/bryshop")
        await self.bot.change_presence(activity=activity)

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command: apc.Command) -> None:
        _log.info(
            f"""
--- Command Completed ---
Command: /{command.name}
User: @{interaction.user} ({interaction.user.id})
Channel: #{interaction.channel} ({interaction.channel.id})
-------------------------"""
        )

    async def on_app_command_error(self, interaction: discord.Interaction, error: apc.AppCommandError) -> None:
        _log.error(error)

        embed = discord.Embed(color=0xE24C4B, description=error)

        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: Bot):
    await bot.add_cog(Event(bot))
