from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from database import db
from states.profile_states import ProfileStates
from database.db import get_matches, get_profile
from keyboards.builders import *
# from keyboards.builders import build_match_keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("matches"))
async def cmd_matches(message: Message, state: FSMContext):
    mutuals = get_matches(message.from_user.id)
    profile = db.get_profile(message.from_user.id)
    gender = profile.get("gender") if profile else "Парень"
    if not mutuals:
        await message.answer("Пока нет взаимных лайков 🙁",
                             reply_markup=build_menu_keyboard(gender))
        return

    await state.update_data(match_ids=mutuals, match_index=0)
    await state.set_state(ProfileStates.MATCHES)
    await show_match_profile(message, state)

async def show_match_profile(src, state: FSMContext):
    data = await state.get_data()
    idx   = data["match_index"]
    mids  = data["match_ids"]
    target = mids[idx]
    prof = get_profile(target)
    user_id = prof["user_id"]
    caption = (
        f"👤 {prof['name']}, {prof['age']} лет\n"
        f"🚻 {prof['gender']} ищет {prof['looking_for']}\n"
        f"📍 {prof['city']}\n"
        f"📝 {prof['bio'][:200]}\n\n"
       # f"[Написать сообщение](tg://user?id={user_id})"
    )
    logger.info(user_id, prof["name"], prof["age"], prof["gender"])

    if isinstance(src, Message):
        await src.answer_photo(
            photo=prof["photo_id"],
            caption=caption,
            reply_markup=build_match_keyboard(user_id),
            parse_mode="MarkdownV2"
        )
    else:
        await src.message.edit_media(
            InputMediaPhoto(media=prof["photo_id"], caption=caption, parse_mode="MarkdownV2"),
            reply_markup=build_match_keyboard(user_id),
        )

@router.callback_query(StateFilter(ProfileStates.MATCHES), F.data=="matches_next")
async def on_match_next(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    idx  = (data["match_index"] + 1) % len(data["match_ids"])
    await state.update_data(match_index=idx)
    await show_match_profile(call, state)
    await call.answer()

@router.callback_query(StateFilter(ProfileStates.MATCHES), F.data=="matches_prev")
async def on_match_prev(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    idx  = (data["match_index"] - 1) % len(data["match_ids"])
    await state.update_data(match_index=idx)
    await show_match_profile(call, state)
    await call.answer()

@router.callback_query(StateFilter(ProfileStates.MATCHES), F.data == "exit_matches")
async def on_exit_browse(callback: types.CallbackQuery, state: FSMContext):
    # Выйти из режима метч
    # await callback.message.delete()  # удаляем последнюю показанную анкету
    await state.set_state(ProfileStates.MENU)
    user_id = callback.from_user.id
    my_profile = db.get_profile(user_id)
    await callback.message.answer("📖 Вы вернулись в меню.", reply_markup=build_menu_keyboard(my_profile['gender']))
