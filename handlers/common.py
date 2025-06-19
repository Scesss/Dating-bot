from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states.profile_states import ProfileStates
from keyboards.builders import build_cancel_keyboard
from keyboards.builders import build_menu_keyboard
from database import db
from aiogram import Bot
import logging


logger = logging.getLogger(__name__)

# Create router for common commands
common_router = Router()



async def show_profile_info(message: types.Message, profile: dict, for_self: bool = True):
    """Отправляет сообщение с информацией анкеты.
    profile – словарь с данными профиля из БД."""
    # Собираем текст

    caption = (
        ( "🌟 Это твоя анкета:\n\n" if for_self else "" ) +
        f"👤 Имя: {profile.get('name', 'N/A')}\n"
        f"🎂 Возраст: {profile.get('age', 'N/A')}\n"
        f"🚻 Пол: {profile.get('gender', 'N/A')}\n"
        f"💘 Ищет: {profile.get('looking_for', 'N/A')}\n"
        f"📍 Город: {profile.get('city') or 'Не указан'}\n"
        f"📖 О себе: { (profile.get('bio') or 'Н/Д')[:1000] }"
    )
    # Отправляем фото с подписью, если есть фото

    try:
        if profile.get('photo_id'):
            await message.answer_photo(profile['photo_id'], caption=caption)
        else:
            await message.answer(caption)
    except Exception as e:
        logger.error(f"Failed to send profile info: {e}")


@common_router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext, bot: Bot):
    member = await bot.get_chat_member(chat_id="@CafeDateInc", user_id=message.from_user.id)
    if member.status in ("left", "kicked"):
        await message.answer("❗️Для работы бота подпишитесь на наш канал: @CafeDateInc")
        return

    await state.clear()
    user_id = message.from_user.id
    logger.info(f"Start command from {user_id}")
    profile = db.get_profile(user_id)


    if profile:
        # Если профиль есть – показываем его
        await message.answer("🌟 Это твоя анкета:", reply_markup=build_menu_keyboard())
        # Устанавливаем состояние меню (пользователь уже зарегистрирован)
        await state.set_state(ProfileStates.MENU)
        # Отправляем данные анкеты пользователю (см. следующий раздел о формате вывода)
        await show_profile_info(message, profile)
    else:
        # Если профиля нет – запускаем регистрацию
        await state.set_state(ProfileStates.NAME)
        await message.answer("Как тебя зовут?", reply_markup=build_cancel_keyboard())

@common_router.message(Command("profile"))
async def cmd_profile(message: types.Message, state: FSMContext):
    await cmd_start(message, state)

# Export the router
__all__ = ['common_router']