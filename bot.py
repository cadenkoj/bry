import logging
import os
from typing import Any

import discord
from discord.ext import commands
from pymongo import MongoClient
from pymongo.database import Database

from utils import LogFormatter

_log = logging.getLogger(__name__)


class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__("b,", help_command=None, intents=intents)
        self.database = self._get_database(name="bry")
        self.log_formatter = LogFormatter()

    # internals

    def _get_database(self, **options: Any) -> Database:
        return MongoClient(os.environ.get("ATLAS_URI")).get_database(**options)

    async def setup_hook(self) -> None:
        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                cog = filename[:-3]
                try:
                    await self.load_extension(f"cogs.{cog}")
                except Exception as e:
                    _log.warning(f"Cog '{cog}' raised an exception: {e.__class__.__name__}: {e}")
