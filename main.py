import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import Config
from handlers import main_router
from aiogram.fsm.storage.memory import MemoryStorage
from handlers.likes   import router as likes_router
from handlers.matches import router as matches_router
from handlers.top import router as top_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


async def main():
    try:
        # Initialize bot
        bot = Bot(
            token=Config.BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )

        # Test token validity
        bot_info = await bot.get_me()
        logger.info(f"Starting bot: @{bot_info.username} [ID: {bot_info.id}]")

        dp = Dispatcher(storage=MemoryStorage())

        @dp.update.outer_middleware()
        async def debug_middleware(handler, event, data):
            logger.debug(f"Received update: {event}")
            result = await handler(event, data)
            return result


        # Include your router with state handlers
        dp.include_router(main_router)
        dp.include_router(likes_router)
        dp.include_router(matches_router)
        dp.include_router(top_router)

        # Start polling
        logger.info("⏳ Starting polling with state management...")
        # logger.info(f"States loaded: {profile_states.__all_states__}")
        await dp.start_polling(bot)

    except Exception as e:
        logger.exception(f"Critical error: {e}")
    finally:
        logger.info("Bot stopped")
        await bot.session.close()


if __name__ == "__main__":
    # init_db()
    asyncio.run(main())