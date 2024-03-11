import os

from dotenv import load_dotenv

from bot import Bot
from utils import setup_logging

load_dotenv()
setup_logging()

bot = Bot()

if __name__ == '__main__':
    bot.run(os.environ.get("TOKEN"), reconnect=True, log_handler=None)
