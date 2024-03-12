import logging
import os

import discord
from discord.ext import commands
from pymongo import MongoClient
from pymongo.database import Database

from utils import ActionCache

_log = logging.getLogger(__name__)


class Bot(commands.Bot):
    def __init__(self):
        from config import BotConfig

        intents = discord.Intents.all()
        super().__init__(",", help_command=None, intents=intents)
        self.config: BotConfig = None
        self.database = self._get_database(name="bry")
        self.action_cache = ActionCache(None, None, None, None, None)

    def _get_database(self, **options) -> Database:
        return MongoClient(os.getenv("ATLAS_URI")).get_database(**options)

    async def setup_hook(self) -> None:
        for root, dirs, files in os.walk("/data"):
            level = root.replace("/data", '').count(os.sep)
            indent = ' ' * 4 * (level)
            print('{}{}/'.format(indent, os.path.basename(root)))
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                print('{}{}'.format(subindent, f))

        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                cog = filename[:-3]
                try:
                    await self.load_extension(f"cogs.{cog}")
                except Exception as e:
                    _log.warning(f"Cog '{cog}' raised an exception: {e.__class__.__name__}: {e}")

        for filename in os.listdir("views"):
            if filename.endswith(".py"):
                view = filename[:-3]
                try:
                    await self.load_extension(f"views.{view}")
                except Exception as e:
                    _log.warning(f"View '{view}' raised an exception: {e.__class__.__name__}: {e}")
