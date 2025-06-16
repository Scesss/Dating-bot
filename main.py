import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database.db import init_db
from handlers.menu import router as menu_router
from handlers.profile import router as profile_router
from handlers.browse import router as browse_router

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(menu_router)
    dp.include_router(profile_router)
    dp.include_router(browse_router)
    await init_db()
    print("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
