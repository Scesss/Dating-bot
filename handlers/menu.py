from aiogram import Router
from aiogram.types import Message
from keyboards.reply import main_menu
from database.db import get_profile
from keyboards.inline import edit_menu

router = Router()

@router.message(lambda message: message.text == "👤 Моя анкета")
async def cmd_profile(message: Message):
    profile = await get_profile(message.from_user.id)
    if profile:
        text = (
            f"👤 <b>Ваша анкета</b>\n"
            f"Имя: {profile['name']}\n"
            f"Пол: {profile['gender']}\n"
            f"О себе: {profile['about']}\n"
            f"Возраст: {profile['age']}\n"
            f"Город: {profile['city']}\n"
            f"Кого ищете: {profile['preference']}"
        )
        await message.answer(text, reply_markup=edit_menu(), parse_mode="HTML")
    else:
        from handlers.profile import start_profile
        await message.answer("Сначала заполните анкету:", reply_markup=None)
        await start_profile(message)
