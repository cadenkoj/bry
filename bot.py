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

    async def setup_hook(self):
        from cogs.Accounting import Accounting

        await self.add_cog(Accounting(self))
