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
    user_id = message.from_user.id
    match_ids = get_matches(user_id)  # из database.db

    if not match_ids:
        # если нет ни одного матча
        profile = get_profile(user_id)
        await message.answer(
            "У вас пока нет матчей.",
            reply_markup=build_menu_keyboard(profile["gender"])
        )
        return

    # сохраняем в FSM
    await state.update_data(match_ids=match_ids, match_index=0)
    await state.set_state(ProfileStates.MATCHES)

    # сразу показываем первый матч
    await show_match_profile(message, state)

@router.message(StateFilter(ProfileStates.MATCHES))
async def show_match_profile(src, state: FSMContext):
    data = await state.get_data()
    idx   = data["match_index"]
    mids  = data["match_ids"]
    target = mids[idx]
    prof = get_profile(target)
    user_id = prof["user_id"]
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
            reply_markup=build_match_keyboard(user_id),
            parse_mode="MarkdownV2"
        )
    else:
        await src.message.edit_media(
            InputMediaPhoto(media=prof["photo_id"], caption=caption, parse_mode="MarkdownV2"),
            reply_markup=build_match_keyboard(user_id),
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
