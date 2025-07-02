from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from database.db import get_all_profiles_sorted_by_balance
from keyboards.builders import *
from states.profile_states import *
from database import db

router = Router()

@router.message(Command("top"))
async def cmd_top(message: Message, state: FSMContext):
    """
    Команда /top — загружает все анкеты, сортированные по balance desc,
    сохраняет в state и показывает первую.
    """
    profiles = get_all_profiles_sorted_by_balance()  # должен возвращать list[dict]
    if not profiles:
        return await message.answer("Пока нет ни одной анкеты.")
    # сохраняем в state
    await state.update_data(top_profiles=profiles, top_index=0)
    await show_top_profile(message, state)


async def show_top_profile(
    message_or_query, state: FSMContext, is_query: bool = False
):
    """
    Универсальная функция: если is_query=True — редактируем предыдущее сообщение,
    иначе — шлём новое.
    """
    data = await state.get_data()
    profiles = data["top_profiles"]
    idx = data["top_index"]
    prof = profiles[idx]

    # формируем текст
    rank = db.get_user_rank(prof['user_id'])
    text = (f"{prof['name']}, "
               f"{prof['age']}, "
               f"{prof['city'] or 'Не указан'}\n\n"
               f" {prof['bio'][:1000]}\n\n"
               f" 🪙 {prof['balance']}, топ {rank}")

    kb = build_top_navigation_keyboard(idx, len(profiles))

    if prof.get("photo_id"):
        if is_query:
            # редактируем текущее сообщение с фото
            await message_or_query.message.edit_media(
                media=InputMediaPhoto(
                    media=prof["photo_id"],
                    caption=text
                ),
                reply_markup=kb,
                parse_mode = None
            )
        else:
            await message_or_query.answer_photo(
                photo=prof["photo_id"],
                caption=text,
                reply_markup=kb,
                parse_mode  = None
            )
    else:
        if is_query:
            await message_or_query.message.edit_text(
                text=text,
                reply_markup=kb
            )
        else:
            await message_or_query.answer(
                text=text,
                reply_markup=kb
            )


@router.callback_query(lambda c: c.data.startswith("top:"))
async def top_navigation(cq: CallbackQuery, state: FSMContext):
    """
    Обработка кнопок «⬅️», «➡️», «❌ Главное меню»
    """
    action = cq.data.split(":", 1)[1]
    data = await state.get_data()
    idx = data["top_index"]
    profiles = data["top_profiles"]
    total = len(profiles)

    if action == "prev":
        idx = (idx - 1) % total
    elif action == "next":
        idx = (idx + 1) % total
    elif action == "exit":
        await state.set_state(ProfileStates.MENU)
        user_id = cq.from_user.id
        my_profile = db.get_profile(user_id)
        await cq.message.answer("📖 Вы вернулись в меню.", reply_markup=build_menu_keyboard(my_profile['gender']))
        return

    await state.update_data(top_index=idx)
    await show_top_profile(cq, state, is_query=True)
    await cq.answer()  # чтобы убрать «часики» у пользователя
