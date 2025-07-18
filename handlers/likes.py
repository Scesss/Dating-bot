from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters.state import StateFilter
from aiogram.fsm.context import FSMContext
from database import db
from states.profile_states import ProfileStates
from handlers.common import show_liked_profile
from keyboards.builders import *
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ReplyKeyboardRemove
from handlers.menu import show_next_profile  
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
    # +1 за ответ на лайк
    change_balance(me, 1)
    # 2) Если взаимный — заматчим
    if user_liked(target, me):
        add_match(me, target)
        # уведомляем инициатора
        my_name     = db.get_profile(me)["name"]
        target_name = db.get_profile(target)["name"]
        
        await call.message.answer(f"🎉 Это взаимный лайк! Жми /matches, чтобы увидеть")

        add_match(target, me)
        # уведомляем получателя

        target_unseen = db.get_unseen_matches_count(target)
        await call.bot.send_message(
            target,
            f"🤝 У вас {target_unseen} непросмотренных матчей!"
        )

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
            "Анкеты закончились ⏳ Возвращаемся в меню…",
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
    me     = call.from_user.id
    target = int(call.data.split(":", 1)[1])

    # Сохраняем дизлайк
    add_dislike(me, target)
    await call.answer("❌ Вы отклонили этот лайк")

    # Если это был последний — возвращаем в меню
    if idx >= len(likers):
        await state.set_state(ProfileStates.MENU)
        try:
            await call.message.delete()
        except TelegramBadRequest:
            pass
        # Возвращаем главное меню (поменяйте build_menu_keyboard на ваш импорт)
        await call.message.answer(
            "Анкеты закончились ⏳ Возвращаемся в меню…",
            reply_markup=build_menu_keyboard(
                db.get_profile(me).get("gender", "Парень")
            )
        )
        return

    # Иначе — показываем следующую анкету из likes
    await state.update_data(likes_index=idx)
    await show_liked_profile(call, state)

@router.callback_query(
    StateFilter(ProfileStates.BROWSING),
    F.data.startswith("dislike:")
)
async def dislike_simple(call: CallbackQuery, state: FSMContext):
    me = call.from_user.id
    target = int(call.data.split(":", 1)[1])
    # Запишем дизлайк
    add_dislike(me, target)
    await call.answer()
    # показать следующий профиль
    await show_next_profile(call, state)
    
# Простой лайк (как было раньше)
@router.callback_query(ProfileStates.BROWSING, F.data.startswith("like_simple:"))
async def like_simple(call: CallbackQuery, state: FSMContext):


    target = int(call.data.split(":")[1])
    add_like(call.from_user.id, target)
    # +1 за то, что ставишь лайк
    change_balance(call.from_user.id, 1)
    # +5 тому, кто получает лайк
    change_balance(target, 5)
    
    if db.user_liked(target, call.from_user.id):
        # Получаем имя оппонента для сообщения (можно было передать через callback или хранить в FSM данные текущей анкеты)
        target_profile = db.get_profile(target)
        name = target_profile['name'] if target_profile else "вам"
        target_unseen = db.get_unseen_matches_count(target)
        await call.bot.send_message(target, f"🤝 У вас {target_unseen} непросмотренных матчей!")
    else:
        unseen = db.get_unseen_count_likes(target)
        await call.bot.send_message(
            target,
            f"❤️ У вас {unseen} непросмотренных лайков!"
        )
    db.check_and_credit_referral(target)
    await call.answer()
    # показать следующий профиль
    await show_next_profile(call, state)

# Лайк + сообщение
@router.callback_query(ProfileStates.BROWSING, F.data.startswith("like_msg:"))
async def like_with_msg_req(call: CallbackQuery, state: FSMContext):
    target = int(call.data.split(":")[1])
    await state.update_data(liked_user_id=target)
    await state.set_state(ProfileStates.LIKE_WITH_MESSAGE)
    cancel_kb = get_cancel_keyboard()
    await call.message.answer("Напишите сообщение, которое будет отправлено вместе с лайком:", reply_markup=cancel_kb)
    await call.answer()

@router.message(ProfileStates.LIKE_WITH_MESSAGE)
async def like_with_msg(msg: Message, state: FSMContext):
    data = await state.get_data()
    target = data.get("liked_user_id")

    # 1) Обработка отмены
    if msg.text == "❌ Отмена":
        # Возвращаем состояние просмотра
        await state.set_state(ProfileStates.BROWSING)
        # Прячем клавиатуру «Отмена»
        await msg.answer("Действие отменено.", reply_markup=ReplyKeyboardRemove())

        # 2) Снова показываем текущую анкету
        profile = db.get_profile(target)
        rank     = db.get_user_rank(target)
        caption = (
            f"{profile['name']}, {profile['age']}, {profile.get('city') or 'Не указан'}\n\n"
            f"{profile.get('bio','')[:1000]}\n\n"
            f"🪙 {profile['balance']}, 📊 топ {rank}"
        )
        # Вставляем клавиатуру лайков/дизлайнов заново
        kb = get_browse_keyboard(target)
        if profile.get("photo_id"):
            await msg.answer_photo(profile["photo_id"], caption=caption, reply_markup=kb)
        else:
            await msg.answer(caption,                reply_markup=kb)
        return


    text   = msg.text[:500]  # обрезаем, если слишком много
    add_like(msg.from_user.id, target, message=text)
    # +2 за лайк с сообщением
    change_balance(msg.from_user.id, 2)
    # +7 тому, кто получает лайк с сообщением
    change_balance(target, 7)
    # уведомляем получателя
    if db.user_liked(target, msg.from_user.id):
        # Получаем имя оппонента для сообщения (можно было передать через callback или хранить в FSM данные текущей анкеты)
        target_profile = db.get_profile(target)
        name = target_profile['name'] if target_profile else "вам"
        target_unseen = db.get_unseen_matches_count(target)
        await msg.bot.send_message(target, f"🤝 У вас {target_unseen} непросмотренных матчей!")
    else:
        unseen = db.get_unseen_count_likes(target)
        await msg.bot.send_message(
            target,
            f"❤️ У вас {unseen} непросмотренных лайков!"
        )
    await msg.answer("Сообщение отправлено вместе с лайком! 👍")
    await state.set_state(ProfileStates.BROWSING)
    await show_next_profile(msg, state)

# Лайк + передача валюты
@router.callback_query(ProfileStates.BROWSING, F.data.startswith("like_cash:"))
async def like_with_cash_req(call: CallbackQuery, state: FSMContext):
    target  = int(call.data.split(":")[1])
    profile = get_user(call.from_user.id)
    bal     = profile["balance"]
    await state.update_data(liked_user_id=target)
    await state.set_state(ProfileStates.LIKE_WITH_CASH)
    await call.message.answer(f"У вас на счету {bal} монет. Введите сумму, которую хотите отправить вместе с лайком:", reply_markup = get_cancel_keyboard())
    await call.answer()

@router.message(ProfileStates.LIKE_WITH_CASH)
async def like_with_cash(msg: Message, state: FSMContext):
    data = await state.get_data()
    target = data.get("liked_user_id")
    # Клавиатура отмены
    cancel_kb = get_cancel_keyboard()

    # Обработка отмены
    if msg.text == "❌ Отмена":
        # Возвращаем состояние просмотра
        await state.set_state(ProfileStates.BROWSING)
        # Прячем клавиатуру «Отмена»
        await msg.answer("Действие отменено.", reply_markup=ReplyKeyboardRemove())

        # 2) Снова показываем текущую анкету
        profile = db.get_profile(target)
        rank     = db.get_user_rank(target)
        caption = (
            f"{profile['name']}, {profile['age']}, {profile.get('city') or 'Не указан'}\n\n"
            f"{profile.get('bio','')[:1000]}\n\n"
            f"🪙 {profile['balance']}, 📊 топ {rank}"
        )
        # Вставляем клавиатуру лайков/дизлайнов заново
        kb = get_browse_keyboard(target)
        if profile.get("photo_id"):
            await msg.answer_photo(profile["photo_id"], caption=caption, reply_markup=kb)
        else:
            await msg.answer(caption,                reply_markup=kb)
        return

    try:
        amount = int(msg.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        return await msg.answer(
            "Пожалуйста, введите положительное число монет или нажмите ❌ Отмена.",
            reply_markup=cancel_kb
        )

    profile = get_user(msg.from_user.id)
    if profile["balance"] < amount:
        return await msg.answer(
            "У вас недостаточно монет. Введите другую сумму или нажмите ❌ Отмена.",
            reply_markup=cancel_kb
        )

    # списываем с отправителя и зачисляем получателю
    change_balance(msg.from_user.id, -amount)
    change_balance(target, amount)
    # +2 за то, что ставишь лайк с валютой
    change_balance(msg.from_user.id, 2)
    # +7 за получение такого лайка
    change_balance(target, 7)
    add_like(msg.from_user.id, target, amount=amount)
    db.check_and_credit_referral(target)

    if db.user_liked(target, msg.from_user.id):
        # Получаем имя оппонента для сообщения (можно было передать через callback или хранить в FSM данные текущей анкеты)
        target_profile = db.get_profile(target)
        name = target_profile['name'] if target_profile else "вам"
        target_unseen = db.get_unseen_matches_count(target)
        await msg.bot.send_message(target, f"🤝 У вас {target_unseen} непросмотренных матчей!")
    else:
        unseen = db.get_unseen_count_likes(target)
        await msg.bot.send_message(
            target,
            f"❤️ У вас {unseen} непросмотренных лайков!"
        )
    await msg.answer(f"Вы отправили лайк и {amount} монет. 💸")
    await state.set_state(ProfileStates.BROWSING)
    await show_next_profile(msg, state)

@router.callback_query(StateFilter(ProfileStates.BROWSING), F.data == "exit_browse")
async def on_exit_browse(callback: types.CallbackQuery, state: FSMContext):
    # Выйти из режима просмотра
    await callback.message.delete()  # удаляем последнюю показанную анкету
    await state.set_state(ProfileStates.MENU)
    user_id = callback.from_user.id
    my_profile = db.get_profile(user_id)
    await callback.message.answer("📖 Вы вернулись в меню.", reply_markup=build_menu_keyboard(my_profile['gender']))
