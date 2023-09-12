import asyncio
import os

from dotenv import load_dotenv

from bot import Bot

load_dotenv()


async def main() -> None:
    bot = Bot()
    await bot.start(os.getenv("DISCORD_TOKEN"))


if __name__ == "__main__":
    asyncio.run(main())
