import asyncio
import logging
import traceback

import discord
from discord import app_commands as apc
from discord.ext import commands

from bot import Bot
from constants import *

_log = logging.getLogger(__name__)

class Event(commands.Cog):
    """Events for handling listeners and startup."""

    def __init__(self, bot: Bot):
        self.bot = bot
        self.bot.tree.error(self.on_app_command_error)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Called when the bot is finished starting up."""

        from config import get_config
        self.bot.config = get_config(self.bot)
    
        _log.info("Logged in as %s (User ID: %d).", self.bot.user, self.bot.user.id)

        before_commands = self.bot.tree.get_commands()
        after_commands = await self.bot.tree.sync()

        _log.info(
            "Successfully synced %d of %d commands.",
            len(after_commands),
            len(before_commands),
        )

        activity = discord.Activity(type=discord.ActivityType.watching, name=".gg/bryshop")
        await self.bot.change_presence(activity=activity)

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command: apc.Command) -> None:
        """Called when an application command runs successfully."""

        _log.info(
            """Command %s completed.
User %s (ID: %d)
Channel %s (ID: %d)""",
            command.name,
            interaction.user,
            interaction.user.id,
            interaction.channel,
            interaction.channel.id,
        )


    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """Called when a command raises an uncaught exception."""

        _log.error(error)
        traceback.print_exc()

        message = str(error.__cause__ or error)
        embed = discord.Embed(color=0xE24C4B, description=f"{EMOJIS.error} {message}")

        message = await ctx.reply(embed=embed, ephemeral=True)
        await asyncio.sleep(5)
        await message.delete()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Called when the bot receives a message."""

        if message.author.bot:
            return

        if message.channel.id == 1213589851065163806:
            embed = discord.Embed(
                color=0xE24C4B,
                description=f"{EMOJIS.error} Please only use commands in this channel.",
            )

            await message.reply(embed=embed, mention_author=True, delete_after=5)
            await asyncio.sleep(5)
            await message.delete()
        

    async def on_app_command_error(self, interaction: discord.Interaction, error: apc.AppCommandError) -> None:
        """Called when an application command raises an uncaught exception."""

        _log.error(error)
        traceback.print_exc()

        message = str(error.__cause__ or error)
        embed = discord.Embed(color=0xE24C4B, description=f"{EMOJIS.error} {message}")

        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: Bot):
    await bot.add_cog(Event(bot))
