from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from states.profile_states import ProfileStates
from keyboards.builders import *
from database import db
from aiogram import Bot
import logging
from aiogram import Bot, Router, types
from database.db import *
from typing import Union
from aiogram.types import Message, CallbackQuery
from aiogram.types import InputMediaPhoto
from handlers.edit_profile import *
# … остальные импорты …




logger = logging.getLogger(__name__)

# Create router for common commands
common_router = Router()



async def show_profile_info(message: types.Message, profile: dict, for_self: bool = True) -> [[int], [list]]:
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
    return [profile['photo_id'], caption]


@common_router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext, bot : Bot):
    member = await bot.get_chat_member(chat_id="@CafeDateInc", user_id=message.from_user.id)
    if member.status in ("left", "kicked"):
        await message.answer("❗️Для работы бота подпишитесь на наш канал: @CafeDateInc")
        return

    await state.clear()
    user_id = message.from_user.id
    logger.info(f"Start command from {user_id}")
    profile = db.get_profile(user_id)


    if profile:
        await message.answer("📄 Хотите начать все с чистого листа?", reply_markup=build_restart_keyboard())
        await state.set_state(ProfileStates.RESTART)
        # # Если профиль есть – показываем его
        # gender = profile["gender"] if profile else "Парень"
        # await message.answer("⏳ Открываем анкету...", reply_markup=build_menu_keyboard(gender))
        # # Устанавливаем состояние меню (пользователь уже зарегистрирован)
        # await state.set_state(ProfileStates.MENU)
        # # Отправляем данные анкеты пользователю (см. следующий раздел о формате вывода)
        # await show_profile_info(message, profile)
    else:
        # Если профиля нет – запускаем регистрацию
        await state.set_state(ProfileStates.NAME)
        await message.answer("Как тебя зовут?", reply_markup=build_cancel_keyboard())

@common_router.message(Command("profile"))
async def cmd_profile(message: types.Message, state: FSMContext, bot : Bot):
    member = await bot.get_chat_member(chat_id="@CafeDateInc", user_id=message.from_user.id)
    if member.status in ("left", "kicked"):
        await message.answer("❗️Для работы бота подпишитесь на наш канал: @CafeDateInc")
        return

    await state.clear()
    user_id = message.from_user.id
    logger.info(f"Start command from {user_id}")
    profile = db.get_profile(user_id)

    if profile:
        # # await show_profile_info(message, profile)
        # photo_id, caption = await show_profile_info(message, profile)
        # # Если профиль есть – показываем его
        # await state.set_state(ProfileStates.EDIT_PROFILE)
        # await on_edit_params(callback=show_profile_info)

        await state.set_state(ProfileStates.EDIT_PROFILE)
        # Убираем клавиатуру меню, чтобы не мешала (опционально)
        await message.answer("⏳ Открываем твою анкету...",
                         reply_markup=types.ReplyKeyboardRemove())
        # Отправляем фото+данные профиля с инлайн-кнопками редактирования
        caption = (f" Имя: {profile['name']}\n"
        f" Возраст: {profile['age']}\n"
        f" Пол: {profile['gender']}\n"
        f" Ищет: {profile['looking_for']}\n"
        f" Город: {profile['city'] or 'Не указан'}\n"
        f" О себе: {profile['bio'][:1000]}")
        if profile.get('photo_id'):
            await message.answer_photo(profile['photo_id'], caption=caption,
            reply_markup=get_edit_menu_kb())
        else:
            await message.answer(caption, reply_markup=get_edit_menu_kb())
    else:
        # Если профиля нет – запускаем регистрацию
        await state.set_state(ProfileStates.NAME)
        await message.answer("Как тебя зовут?", reply_markup=build_cancel_keyboard())

async def show_liked_profile(src: Union[Message, CallbackQuery], state: FSMContext):
    data = await state.get_data()
    idx = data["likes_index"]
    likers = data["liked_ids"]
    target_id = likers[idx]

    # Pull their full profile
    prof = db.get_profile(target_id)
    text = (
        f"👤 {prof['name']}, {prof['age']} лет\n"
        f"🚻 {prof['gender']} ищет {prof['looking_for']}\n"
        f"📍 {prof['city']}\n"
        f"📝 {prof['bio'][:200]}"
    )
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="❤️ Поставить лайк",
                callback_data=f"likes_accept:{target_id}"
            ),
            InlineKeyboardButton(
                text="💔 Дизлайк",
                callback_data=f"likes_decline:{target_id}"
            )
        ]]
    )
    if isinstance(src, Message):
        await src.answer_photo(photo=prof["photo_id"], caption=text, reply_markup=kb)
    else:  # CallbackQuery
        await src.message.edit_media(
            InputMediaPhoto(media=prof["photo_id"], caption=text),
            reply_markup=kb
        )

@common_router.message(Command("likes"))
async def cmd_likes(message: types.Message, state: FSMContext):
    # 1) Fetch who liked me
    likers = get_liked_by(message.from_user.id)
    profile = db.get_profile(message.from_user.id)
    gender = profile["gender"] if profile else "Парень"
    if not likers:
        await message.answer(
            "Новых лайков нет ⏳ Возвращаемся в меню…",
            reply_markup=build_menu_keyboard(gender)
        )
        return

    # 2) Save into state: list + cursor index
    await state.update_data(liked_ids=likers, likes_index=0)
    await state.set_state(ProfileStates.LIKES)

    # 3) Show first profile
    await show_liked_profile(message, state)


# Export the router
__all__ = ['common_router']