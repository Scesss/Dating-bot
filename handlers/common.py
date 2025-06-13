from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from states.profile_states import ProfileStates

common_router = Router()

@common_router.message(F.command == "start")
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🌟 Welcome to Dating Bot! Let's create your profile.\n"
        "We'll ask you a few questions to find perfect matches.\n\n"
        "What's your name?"
    )
    await state.set_state(ProfileStates.NAME)

@common_router.message(F.command == "cancel")
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Action canceled", reply_markup=types.ReplyKeyboardRemove())