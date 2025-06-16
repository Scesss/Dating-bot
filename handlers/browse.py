from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from keyboards.reply import main_menu
from keyboards.inline import browse_buttons
from database.db import get_other_profiles, save_like, get_profile, get_liked_by
from utils.utils import prioritize_profiles

router = Router()
browse_sessions = {}

@router.message(lambda message: message.text == "🔍 Просмотр анкет")
async def cmd_browse(message: Message):
    user_id = message.from_user.id
    profiles = await get_other_profiles(user_id)
    current = await get_profile(user_id)
    pref_match, others = prioritize_profiles(profiles, current)
    combined = pref_match + others
    browse_sessions[user_id] = (combined, 0)
    if combined:
        p = combined[0]
        text = (f"👤 <b>{p['name']}</b> ({p['gender']}, {p['age']} лет)\n"
                f"{p['city']}\n📝 {p['about']}")
        await message.answer(text, reply_markup=browse_buttons(p['user_id']), parse_mode="HTML")
    else:
        await message.answer("Нет анкет для просмотра.", reply_markup=main_menu())

@router.callback_query(F.data.startswith("like:"))
async def process_like(call: CallbackQuery, bot: Bot):
    user_id = call.from_user.id
    target = int(call.data.split(":",1)[1])
    await save_like(user_id, target)
    if user_id in await get_liked_by(target):
        prof1 = await get_profile(user_id)
        prof2 = await get_profile(target)
        uname1 = prof1['username'] or ""
        uname2 = prof2['username'] or ""
        await call.message.answer(f"Это матч! Ваш контакт: @{uname2}")
        await bot.send_message(target, f"Это матч! Ваш контакт: @{uname1}")
    await call.answer("Лайк!")
    combined, idx = browse_sessions[user_id]
    idx += 1
    if idx < len(combined):
        browse_sessions[user_id] = (combined, idx)
        p = combined[idx]
        text = (f"👤 <b>{p['name']}</b> ({p['gender']}, {p['age']} лет)\n"
                f"{p['city']}\n📝 {p['about']}")
        await call.message.answer(text, reply_markup=browse_buttons(p['user_id']), parse_mode="HTML")
    else:
        await call.message.answer("Анкеты закончились.", reply_markup=main_menu())

@router.callback_query(F.data.startswith("skip:"))
async def process_skip(call: CallbackQuery):
    user_id = call.from_user.id
    combined, idx = browse_sessions[user_id]
    idx += 1
    if idx < len(combined):
        browse_sessions[user_id] = (combined, idx)
        p = combined[idx]
        text = (f"👤 <b>{p['name']}</b> ({p['gender']}, {p['age']} лет)\n"
                f"{p['city']}\n📝 {p['about']}")
        await call.message.answer(text, reply_markup=browse_buttons(p['user_id']), parse_mode="HTML")
    else:
        await call.message.answer("Анкеты закончились.", reply_markup=main_menu())
