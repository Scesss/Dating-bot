# Updated main.py for aiogram 3.x on Python 3.13
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from config import Config
from handlers import router  # Changed to router-based approach

logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=Config.BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    # Include routers
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())