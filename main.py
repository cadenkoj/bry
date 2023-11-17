import os

from dotenv import load_dotenv

from bot import Bot
from config import get_config
from utils import setup_logging

load_dotenv()
setup_logging()

bot = Bot()
bot.run(os.environ.get("TOKEN"), reconnect=True, log_handler=None)
