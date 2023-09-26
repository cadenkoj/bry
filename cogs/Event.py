import discord
from discord import app_commands as apc
from discord.ext import commands

from bot import Bot


class Event(commands.Cog):
    """Events for handling listeners and startup."""

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as {self.user} ({self.user.id})")

        app_commands = self.tree.get_commands()
        commands = len(app_commands)
        print(f"Started syncing {commands} commands.")

        app_commands = await self.tree.sync()
        commands = len(app_commands)
        print(f"Successfully synced {commands} commands.")

        activity = discord.Activity(type=discord.ActivityType.watching, name="over Bry's Shop")
        await self.change_presence(activity=activity)

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command: apc.Command) -> None:
        print(
            f"""
--- Command Completed ---
Command: /{command.name}
User: @{interaction.user} ({interaction.user.id})
Channel: #{interaction.channel} ({interaction.channel.id})
-------------------------
"""
        )

    @commands.Cog.listener()
    async def on_app_command_error(self, interaction: discord.Interaction, error: apc.AppCommandError) -> None:
        print(error)

        embed = discord.Embed(color=0xE24C4B, description=error)

        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)
