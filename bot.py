import os

import discord
from discord import app_commands as apc
from discord.ext import commands
from pymongo import MongoClient


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(",", help_command=None, intents=intents)
        self.database = self._get_database(name="bry")

        self.event(self.on_ready)
        self.event(self.on_app_command_completion)

        self.tree.error(self.on_app_command_error)

    def _get_database(self, name: str):
        mongo_uri = os.getenv("MONGO_URI")

        if mongo_uri is None:
            raise ValueError("MongoDB URI is not defined.")

        client = MongoClient(mongo_uri)
        return client.get_database(name)

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

    async def on_app_command_completion(self, interaction: discord.Interaction, command: apc.Command) -> None:
        print(
            f"""
--- Command Completed ---
Command: /{command.name}
User: @{interaction.user} ({interaction.user.id})
Channel: #{interaction.channel} ({interaction.channel.id})
"""
        )

    async def on_app_command_error(self, interaction: discord.Interaction, error: apc.AppCommandError) -> None:
        print(error)

        embed = discord.Embed(color=0xE24C4B, description=error)

        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def setup_hook(self):
        from cogs.accounting import Accounting

        await self.add_cog(Accounting(self))
