from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from states.profile_states import ProfileStates
from keyboards.builders import *
from aiogram.filters import StateFilter
from database import db
from aiogram import Bot
import logging
from handlers.top import cmd_top
from aiogram.types import CallbackQuery, Message

logger = logging.getLogger(__name__)



router = Router()

@router.message(StateFilter(ProfileStates.MENU))
async def process_choose(message: types.Message, state: FSMContext):
    valid_answer = ["🔍 Смотреть Анкеты", "👨🏼 Моя Анкета", "👑 Топ", "🌙 Сон", "👩🏻‍🦰 Моя Анкета"]
    if message.text not in valid_answer:
        return await message.answer("Нет такого варианта ответа")

    elif message.text == "👨🏼 Моя Анкета" or message.text == "👩🏻‍🦰 Моя Анкета":
        # Переходим в режим редактирования профиля
        await state.set_state(ProfileStates.EDIT_PROFILE)
        # Убираем клавиатуру меню, чтобы не мешала (опционально)
        await message.answer("⏳ Открываем твою анкету...",
                         reply_markup=types.ReplyKeyboardRemove())
        # Получаем профиль из базы
        profile = db.get_profile(message.from_user.id)
        if profile:
        # Отправляем фото+данные профиля с инлайн-кнопками редактирования
            caption = (f"{profile['name']}, "
                   f"{profile['age']}, "
                   f"{profile['city'] or 'Не указан'}\n\n"
                   f" {profile['bio'][:1000]}\n\n"
                   f" 🪙 {profile['balance']}, топ 2228")
            if profile.get('photo_id'):
                await message.answer_photo(profile['photo_id'], caption=caption,
                                   reply_markup=get_edit_menu_kb())
            else:
                await message.answer(caption, reply_markup=get_edit_menu_kb())
        else:
            await message.answer("У вас ещё нет анкеты. Введите /start для регистрации.")
    elif message.text == "🔍 Смотреть Анкеты":
        # Переходим в режим просмотра чужих анкет
        await state.set_state(ProfileStates.BROWSING)
        # Убираем меню-клавиатуру
        await message.answer("⏳ Поиск анкет...",
                             reply_markup=types.ReplyKeyboardRemove())
        # Получаем собственный профиль (для критериев поиска)
        my_profile = db.get_profile(message.from_user.id)
        if not my_profile:
            await message.answer("У вас нет анкеты для поиска. Сначала создайте анкету.")
            await state.clear()
            return
        # Ищем первую подходящую анкету
        logger.info("get_next_profile(simple) → %r", my_profile)
        result = db.get_next_profile(
            current_user_id    = message.from_user.id,
            current_gender     = my_profile['gender'],
            current_preference = my_profile['looking_for'],
            user_lat           = my_profile['lat'],
            user_lon           = my_profile['lon']
        )
        if result:
            text = (f"{result['name']}, {result['age']}, {result.get('city') or 'Не указан'}, ")
            if result['distance_km'] is not None:
                text += f"📍 {result['distance_km']} км"
            text += f"\n\n{result['bio'][:200]}"
        # Ограничим био ~300 символов, чтобы не перегружать сообщение
            try:
                if result.get('photo_id'):
                    await message.answer_photo(result['photo_id'], caption=text, reply_markup=get_browse_keyboard(result['user_id']))
                else:
                    await message.answer(text,
                             reply_markup=get_browse_keyboard(result['user_id']))
            except Exception as e:
                logger.error(f"Failed to send profile {result['user_id']}: {e}")
        else:
            profile = db.get_profile(message.from_user.id)
            gender = profile['gender']
            await message.answer("Сейчас нет анкет, соответствующих вашим параметрам.", reply_markup=build_menu_keyboard(gender))
            await state.set_state(ProfileStates.MENU)
    elif message.text == "🌙 Сон":
        return await message.answer("Пока нет такой функции")
    elif message.text == "👑 Топ":
        await cmd_top(message, state)



async def show_next_profile(event: CallbackQuery | Message, state: FSMContext):
    """
    Показывает следующую анкету.
    Принимает либо CallbackQuery (нажатие кнопки), либо Message (после FSM).
    """

    # 1) Ack + убрать старую клавиатуру
    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.edit_reply_markup(reply_markup=None)
        user_id = event.from_user.id
        send_photo = event.message.answer_photo
        send_text  = event.message.answer
    else:
        user_id = event.from_user.id
        send_photo = event.answer_photo
        send_text  = event.answer

    # 2) Берём свой профиль (содержит все поля)
    current = db.get_user(user_id)
    if not current:
        await send_text("❗ Сначала создайте профиль командой /start")
        return

    # 3) Берём фильтры и координаты
    gender     = current.get("gender")
    preference = current.get("looking_for")
    lat        = current.get("lat")
    lon        = current.get("lon")

    if not gender or not preference:
        await send_text("❗ Заполните пол и предпочтение в профиле.")
        return

    # 4) Достаём следующую анкету
    try:
        result = db.get_next_profile(
            current_user_id    = user_id,
            current_gender     = gender,
            current_preference = preference,
            user_lat           = lat,
            user_lon           = lon
        )
    except Exception as e:
        logger.error(f"Ошибка get_next_profile: {e}")
        await send_text("⚠️ Не удалось загрузить следующую анкету, попробуйте позже.")
        return

    # 5) Проверка результата
    if not result:
        await send_text("😢 Больше анкет не найдено.")
        await state.clear()
        return

    # 6) Подготовка полей
    name = result.get("name", "—")
    age  = result.get("age", "—")
    looking_for = result.get("looking_for", "—")
    city = result.get("city", "—")

    # distance_km может быть None
    dist = result.get("distance_km")
    if dist is None:
        distance_str = "🚗 расстояние неизвестно"
    else:
        distance_str = f"🚗 {dist:.1f} км"

    # balance может быть None
    balance = result.get("balance")
    if balance is None:
        balance_str = "🪙 0"
    else:
        balance_str = f"🪙 {balance}"

    bio = result.get("bio")
    bio_str = f"\n{bio}" if bio else ""

    # 7) Собираем текст
    text = (
        f"👤 {name}, {age}\n"
        f"💖 Ищет: {looking_for}\n"
        f"📍 Город: {city}\n"
        f"{distance_str}\n"
        f"{balance_str}"
        f"{bio_str}"
    )

    # 8) Клавиатура
    kb = get_browse_keyboard(result["user_id"])

    # 9) Отправка профиля
    photo = result.get("photo_id")
    if photo:
        await send_photo(photo=photo, caption=text, reply_markup=kb)
    else:
        await send_text(text, reply_markup=kb)

    # 10) Устанавливаем состояние
    await state.set_state(ProfileStates.BROWSING)




