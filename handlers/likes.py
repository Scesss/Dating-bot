from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from database import db
from states.profile_states import ProfileStates
from handlers.common import show_liked_profile
from keyboards.builders import *
from aiogram.exceptions import TelegramBadRequest
from database.db import *

router = Router()

@router.callback_query(
    StateFilter(ProfileStates.LIKES),
    F.data.startswith("likes_accept:")
)
async def on_like_accept(call: CallbackQuery, state: FSMContext):
    data   = await state.get_data()
    likers = data.get("liked_ids", [])
    idx    = data.get("likes_index", 0) + 1
    me = call.from_user.id
    target = int(call.data.split(":", 1)[1])
    # 1) Запишем свой лайк
    add_like(me, target)
    # 2) Если взаимный — заматчим
    if user_liked(target, me):
        add_match(me, target)
        add_match(target, me)

    # Когда кандидаты кончились — удаляем сообщение и возвращаем меню
    if idx >= len(likers):
        await state.set_state(ProfileStates.MENU)
        # попробуем удалить старое сообщение-карточку
        try:
            await call.message.delete()
        except TelegramBadRequest:
            pass
        # покажем главное меню
        profile = db.get_profile(call.from_user.id)
        gender  = profile.get("gender") if profile else "Парень"
        await call.message.answer(
            "Новых лайков нет ⏳ Возвращаемся в меню…",
            reply_markup=build_menu_keyboard(gender)
        )
        await state.set_state(ProfileStates.MENU)
        await call.answer()
        return

    # Иначе — показываем следующую анкету
    await state.update_data(likes_index=idx)
    await show_liked_profile(call, state)
    await call.answer()


@router.callback_query(
    StateFilter(ProfileStates.LIKES),
    F.data.startswith("likes_decline:")
)
async def on_like_decline(call: CallbackQuery, state: FSMContext):
    data   = await state.get_data()
    likers = data.get("liked_ids", [])
    idx    = data.get("likes_index", 0) + 1
    me = call.from_user.id
    target = int(call.data.split(":", 1)[1])

    # Запишем дизлайк
    add_dislike(me, target)
    # Когда кандидаты кончились
    if idx >= len(likers):
        await state.set_state(ProfileStates.MENU)
        try:
            await call.message.delete()
        except TelegramBadRequest:
            pass
        profile = db.get_profile(call.from_user.id)
        gender  = profile.get("gender") if profile else "Парень"
        await call.message.answer(
            "Новых лайков нет ⏳ Возвращаемся в меню…",
            reply_markup=build_menu_keyboard(gender)
        )
        await state.set_state(ProfileStates.MENU)
        await call.answer()
        return

    # Иначе — следующая анкета
    await state.update_data(likes_index=idx)
    await show_liked_profile(call, state)
    await call.answer()
