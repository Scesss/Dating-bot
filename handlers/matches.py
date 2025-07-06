from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from database import db
from states.profile_states import ProfileStates
from database.db import get_matches, get_profile
from keyboards.builders import *
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.geo import calculate_distance
from aiogram.exceptions import TelegramBadRequest
from aiogram import types

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
    me = get_profile(src.from_user.id)

    if me.get("lat") and prof.get("lat") and me.get("lon") and prof.get("lon"):
        
        prof["distance_km"] = calculate_distance(
            me["lat"], me["lon"], prof["lat"], prof["lon"]
        )
    else:
        prof["distance_km"] = None

    if len(mids) > 1:
        kb = build_match_keyboard(user_id)
    else:
        
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
    rank = db.get_user_rank(prof['user_id'])
    caption = f"{prof['name']}, {prof['age']}, {prof.get('city') or 'Не указан'}"
    if prof.get("distance_km") is not None:
        caption += f", 📍 {prof['distance_km']:.1f} км"
    caption += (
        f"\n\n{prof.get('bio', '')[:1000]}\n\n"
        f" _🪙 {prof['balance']}, 📊 топ  {rank}_"
    )
    # logger.info(
    #     "Showing match profile — user_id=%s, name=%s, age=%s, gender=%s",
    #     user_id,
    #     prof["name"],
    #     prof["age"],
    #     prof["gender"],
    #     prof["count_likes"]
    # )

    if isinstance(src, Message):
        await src.answer_photo(
            photo=prof["photo_id"],
            caption=caption,
            reply_markup=kb,
            parse_mode = None
        )
    else:
        try:
            await src.message.edit_media(
                InputMediaPhoto(
                    media=prof["photo_id"],
                    caption=caption,
                    parse_mode=None
                ),
                reply_markup=kb,
                parse_mode=None
            )
        except TelegramBadRequest as e:
            # игнорируем ошибку, когда контент не изменился
            if "message is not modified" in str(e):
                return
            # все остальные пробрасываем дальше
            raise

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
