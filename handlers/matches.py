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

@router.message(StateFilter(ProfileStates.MATCHES))
async def show_match_profile(src, state: FSMContext):
    data = await state.get_data()
    idx   = data["match_index"]
    mids  = data["match_ids"]
    target = mids[idx]
    prof = get_profile(target)
    user_id = prof["user_id"]

    if len(mids) > 1:
        kb = build_match_keyboard(user_id)
    else:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="💌 Написать этому человеку",
                url=f"tg://user?id={user_id}"
            )],
            [InlineKeyboardButton(
                text="◀ Выйти в меню",
                callback_data="exit_matches"
            )]
        ])

    caption = (f"{prof['name']}, "
               f"{prof['age']}, "
               f"{prof['city'] or 'Не указан'}\n\n"
               f" {prof['bio'][:1000]}\n\n"
               f" 🪙 {prof['balance']}, топ 2228")
    logger.info(
        "Showing match profile — user_id=%s, name=%s, age=%s, gender=%s",
        user_id,
        prof["name"],
        prof["age"],
        prof["gender"],
    )

    if isinstance(src, Message):
        await src.answer_photo(
            photo=prof["photo_id"],
            caption=caption,
            reply_markup=kb,
            parse_mode="MarkdownV2"
        )
    else:
        await src.message.edit_media(
            InputMediaPhoto(media=prof["photo_id"], caption=caption, parse_mode="MarkdownV2"),
            reply_markup=kb,
        )

@router.callback_query(
    StateFilter(ProfileStates.MATCHES),
    F.data == "matches_next"
)
async def on_match_next(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    idx  = (data["match_index"] + 1) % len(data["match_ids"])
    await state.update_data(match_index=idx)
    await show_match_profile(call, state)
    await call.answer()

@router.callback_query(
    StateFilter(ProfileStates.MATCHES),
    F.data == "matches_prev"
)
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
