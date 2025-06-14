from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states.profile_states import ProfileStates
import logging

logger = logging.getLogger(__name__)

# Create router for common commands
common_router = Router()

@common_router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    logger.info(f"Start command from {message.from_user.id}")
    await message.answer("🌟 Welcome! Type /profile to create your profile")

@common_router.message(Command("profile"))
async def cmd_profile(message: types.Message, state: FSMContext):
    logger.info(f"Profile command from {message.from_user.id}")
    await state.set_state(ProfileStates.NAME)
    await message.answer("Let's create your profile! What's your name?")

# Export the router
__all__ = ['common_router']