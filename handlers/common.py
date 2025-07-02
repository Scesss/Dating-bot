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
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.types import InputMediaPhoto
from handlers.edit_profile import *
from database.db import user_disliked
from .matches import show_match_profile
from handlers.menu import show_next_profile

# … остальные импорты …




logger = logging.getLogger(__name__)

# Create router for common commands
common_router = Router()

@router.message(Command("search"))
async def cmd_search(message: Message, state: FSMContext):
    """
    /search — то же, что просмотр анкет из меню.
    """
    # Сбрасываем всё и запускаем показ первой анкеты
    await state.clear()
    await message.answer("🔍 Начинаем поиск анкет...")
    # Просто вызываем ту же функцию, что и при просмотре из меню
    await show_next_profile(message, state)


async def show_profile_info(message: types.Message, profile: dict, for_self: bool = True) -> [[int], [list]]:
    """Отправляет сообщение с информацией анкеты.
    profile – словарь с данными профиля из БД."""
    # Собираем текст
    rank = db.get_user_rank(profile['user_id'])
    caption = (f"{profile['name']}, "
               f"{profile['age']}, "
               f"{profile['city'] or 'Не указан'}\n\n"
               f" {profile['bio'][:1000]}\n\n"
               f" 🪙 {profile['balance']}, топ {rank}")
    # Отправляем фото с подписью, если есть фото

    try:
        if profile.get('photo_id'):
            await message.answer_photo(profile['photo_id'], caption=caption, parse_mode  = None)
        else:
            await message.answer(caption)
    except Exception as e:
        logger.error(f"Failed to send profile info: {e}")
    return [profile['photo_id'], caption]


@common_router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext, bot : Bot):

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
        rank = db.get_user_rank(profile['user_id'])
        caption = (f"{profile['name']}, "
        f"{profile['age']}, "
        f"{profile['city'] or 'Не указан'}\n\n"
        f" {profile['bio'][:1000]}\n\n"
        f" 🪙 {profile['balance']}, топ {rank}")
        if profile.get('photo_id'):
            await message.answer_photo(profile['photo_id'], caption=caption,
            reply_markup=get_edit_menu_kb(), parse_mode  = None)
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
    prof   = likers[idx]           # сразу берём всю запись профиля + like_message + like_amount
    target_id = prof["user_id"]

    rank = db.get_user_rank(prof['user_id'])
    text = (f"{prof['name']}, {prof['age']}, {prof.get('city') or 'Не указан'}")
    if prof.get("distance_km") is not None:
        text += f", 📍 {prof['distance_km']:.1f} км"
    text += (f"\n\n{prof['bio'][:200]}\n\n"
                    f" 🪙 {prof['balance']}, топ {rank}")
    
    # если был текстовый лайк
    if prof.get("like_amount"):
        text += f"\n\n💰 Передано: {prof['like_amount']} монет"
    # если оставили сообщение
    if prof.get("like_message"):
        text += f"\n\n💬 «{prof['like_message']}»"
    
    kb = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="❤️ Поставить лайк",
                callback_data=f"likes_accept:{prof['user_id']}"
            ),
            InlineKeyboardButton(
                text="💔 Дизлайк",
                callback_data=f"likes_decline:{prof['user_id']}"
            )
        ]]
    )
    if isinstance(src, Message):
        await src.answer_photo(photo=prof["photo_id"], caption=text, reply_markup=kb, parse_mode  = None)
    else:  # CallbackQuery
        await src.message.edit_media(
            InputMediaPhoto(media=prof["photo_id"], caption=text),
            reply_markup=kb,
            parse_mode  = None
        )

@common_router.message(Command("likes"))
async def cmd_likes(message: types.Message, state: FSMContext):
    me = message.from_user.id
    # 1) Извлекаем всех, кто лайкнул вас
    raw = get_liked_by(me)

    # 2) Фильтруем тех, кого вы уже лайкнули или дизлайкнули
    likers = [
        prof for prof in raw
        if not user_liked(me, prof['user_id'])
        and not user_disliked(me, prof['user_id'])
    ]

    db.mark_likes_seen(me)

    profile = db.get_profile(me)
    gender = profile["gender"] if profile else "Парень"

    if not likers:
        await message.answer(
            "Новых лайков нет ⏳ Возвращаемся в меню…",
            reply_markup=build_menu_keyboard(gender)
        )
        return

    # 3) Сохраняем в state отфильтрованный список
    await state.update_data(liked_ids=likers, likes_index=0)
    await state.set_state(ProfileStates.LIKES)

    # 4) Показываем первую анкету
    await show_liked_profile(message, state)

@common_router.message(Command("matches"))
async def cmd_matches(message: Message, state: FSMContext):
    user_id = message.from_user.id
    match_ids = db.get_matches(user_id)  # из database.db

    if not match_ids:
        # если нет ни одного матча
        profile = db.get_profile(user_id)
        await message.answer(
            "У вас пока нет матчей.",
            reply_markup=build_menu_keyboard(profile["gender"])
        )
        await state.set_state(ProfileStates.MENU)
        return

    # сохраняем в FSM
    await state.update_data(match_ids=match_ids, match_index=0)
    await state.set_state(ProfileStates.MATCHES)

    # сразу показываем первый матч
    await show_match_profile(message, state)

@common_router.message(Command("menu"))
async def cmd_menu(message: types.Message, state: FSMContext, bot : Bot):
    member = await bot.get_chat_member(chat_id="@CafeDateInc", user_id=message.from_user.id)

    if member.status in ("left", "kicked"):
        await message.answer("❗️Для работы бота подпишитесь на наш канал: @CafeDateInc")
        return

    user_id = message.from_user.id
    unseen_likes   = db.get_unseen_likes_count(user_id)
    unseen_matches= db.get_unseen_matches_count(user_id)
    notify_parts = []
    if unseen_likes:
        notify_parts.append(f"❤️ У вас {unseen_likes} непросмотренных лайков")
    if unseen_matches:
        notify_parts.append(f"🤝 У вас {unseen_matches} непросмотренных матчей")
    if notify_parts:
        # после показа уведомления можно отметить их как «увиденные»
        await message.answer("\n".join(notify_parts))
        db.mark_likes_seen(user_id)
        db.mark_matches_seen(user_id)

    await state.clear()
    user_id = message.from_user.id
    logger.info(f"Start command from {user_id}")
    profile = db.get_profile(user_id)

    if profile:
        await state.set_state(ProfileStates.MENU)
        user_id = message.from_user.id
        profile = get_profile(user_id)
        rank = db.get_user_rank(profile['user_id'])
        text = (f"{profile['name']}, "
                   f"{profile['age']}, "
                   f"{profile['city'] or 'Не указан'}\n\n"
                   f" {profile['bio'][:1000]}\n\n"
                   f" 🪙 {profile['balance']}, топ {rank}")
        await message.answer(
            text="⏳ Загружаю ваш профиль…", 
            reply_markup=ReplyKeyboardRemove()
        )
        menu_kb = build_menu_keyboard(profile["gender"])
        if profile.get('photo_id'):
            await message.answer_photo(
                photo=profile["photo_id"],
                caption=text,
                reply_markup=menu_kb,
                parse_mode  = None
            )
        else:
            await message.answer(
                text=text,
                reply_markup=menu_kb
            )

    else:
        # Если профиля нет – запускаем регистрацию
        await state.set_state(ProfileStates.NAME)
        await message.answer("Как тебя зовут?", reply_markup=build_cancel_keyboard())


# Export the router
__all__ = ['common_router']