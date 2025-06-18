from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from handlers.common import cmd_profile
from states.profile_states import ProfileStates
from keyboards.builders import *
from aiogram.filters import StateFilter
from database import db
from aiogram import Bot
import logging

logger = logging.getLogger(__name__)



router = Router()

@router.message(StateFilter(ProfileStates.MENU))
async def process_choose(message: types.Message, state: FSMContext):
    valid_answer = ["Смотреть Анкеты", "Моя Анкета", "Топ", "Сон"]
    if message.text not in valid_answer:
        return await message.answer("Нет такого варианта ответа")

    elif message.text == "Моя Анкета":
        # Переходим в режим редактирования профиля
        await state.set_state(ProfileStates.EDIT_PROFILE)
        # Убираем клавиатуру меню, чтобы не мешала (опционально)
        await message.answer(" Открываем твою анкету...",
                         reply_markup=types.ReplyKeyboardRemove())
        # Получаем профиль из базы
        profile = db.get_profile(message.from_user.id)
        if profile:
        # Отправляем фото+данные профиля с инлайн-кнопками редактирования
            caption = (f" Имя: {profile['name']}\n"
               f" Возраст: {profile['age']}\n"
               f" Пол: {profile['gender']}\n"
               f" Ищет: {profile['looking_for']}\n"
               f" Город: {profile['city'] or 'Не указан'}\n"
               f" О себе: {profile['bio'][:1000]}")
            if profile.get('photo_id'):
                await message.answer_photo(profile['photo_id'], caption=caption,
                                   reply_markup=get_edit_menu_kb())
            else:
                await message.answer(caption, reply_markup=get_edit_menu_kb())
        else:
            await message.answer("У вас ещё нет анкеты. Введите /start для регистрации.")
    elif message.text == "Смотреть Анкеты":
        # Переходим в режим просмотра чужих анкет
        await state.set_state(ProfileStates.BROWSING)
        # Убираем меню-клавиатуру
        await message.answer(" Поиск анкет...",
                             reply_markup=types.ReplyKeyboardRemove())
        # Получаем собственный профиль (для критериев поиска)
        my_profile = db.get_profile(message.from_user.id)
        if not my_profile:
            await message.answer("У вас нет анкеты для поиска. Сначала создайте анкету.")
            await state.clear()
            return
        # Ищем первую подходящую анкету
        result = db.get_next_profile(
            current_user_id=message.from_user.id,
            current_gender=my_profile['gender'],
            current_preference="Парни" if my_profile['looking_for'] == "Парни"
            else "Девушки",
            current_city = my_profile['city'] or 'Не указан',
            current_lat = my_profile['lat'],
            current_lon = my_profile['lon']
        )
        if result:
            text = (f"{result['name']}, {result['age']}, {result.get('city') or 'Не указан'}\n\n"
                f"{ (result.get('bio') or 'Н/Д')[:300] }")
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
            await message.answer("Сейчас нет анкет, соответствующих вашим параметрам.")
            await state.clear()
            await message.answer(" Возвращение в меню.", reply_markup=build_menu_keyboard())
    elif message.text == "Сон":
        return await message.answer("Пока такой функции нет")
    elif message.text == "Топ":
        return await message.answer("Пока такой функции нет")

async def show_next_profile(callback: types.CallbackQuery):
    """Отображает следующую анкету в режиме просмотра или завершает просмотр, если анкет нет."""
    # Удаляем старое сообщение анкеты (текущее) перед показом следующей
    try:
        await callback.message.delete()
    except:
        pass
    user_id = callback.from_user.id
    my_profile = db.get_profile(user_id)
    result = None
    if my_profile:
        result = db.get_next_profile(current_user_id=user_id,
            current_gender=my_profile['gender'],
            current_preference="Парни" if my_profile['looking_for'] == "Парни"
            else "Девушки",
            current_city = my_profile['city'] or 'Не указан',
            current_lat = my_profile['lat'],
            current_lon = my_profile['lon'])
    if result:
        # Отправляем следующую анкету
        text = (f"{result['name']}, {result['age']}, {result.get('city') or 'Не указан'}\n\n"
                f"{ (result.get('bio') or 'Н/Д')[:300] }")
        try:
            if result.get('photo_id'):
                await callback.message.answer_photo(result['photo_id'], caption=text,
                                                    reply_markup=get_browse_keyboard(result['user_id']))
            else:
                await callback.message.answer(text, reply_markup=get_browse_keyboard(result['user_id']))
        except Exception as e:
            logger.error(f"Failed to send profile {result['user_id']}: {e}")
    else:
        # Нет больше анкет
        await callback.message.answer("Анкет больше не найдено.", reply_markup=build_menu_keyboard())
        # Выходим из режима просмотра
        await callback.answer()  # закрываем иконку загрузки на кнопке
        await callback.bot.delete_state(callback.from_user.id)  # очистить FSM state


@router.callback_query(StateFilter(ProfileStates.BROWSING), F.data.startswith("like_"))
async def on_like(callback: types.CallbackQuery, state: FSMContext):
    target_id = int(callback.data.split("_")[1])
    current_user = callback.from_user.id
    db.add_like(current_user, target_id)
    # Проверка взаимного лайка
    if db.user_liked(target_id, current_user):
        # Получаем имя оппонента для сообщения (можно было передать через callback или хранить в FSM данные текущей анкеты)
        target_profile = db.get_profile(target_id)
        name = target_profile['name'] if target_profile else "вам"
        # Уведомление текущему пользователю
        await callback.message.answer(f"❤️ У вас взаимная симпатия с {name}!")
        # Уведомление второму пользователю о совпадении
        try:
            bot = Bot.get_current()
            user_name = (db.get_profile(current_user) or {}).get('name', 'вам')
            await bot.send_message(target_id, f"❤️ У вас взаимная симпатия с {user_name}!")
        except Exception as e:
            logger.error(f"Failed to notify user {target_id} about match: {e}")
    # Показ следующей анкеты
    await show_next_profile(callback)

@router.callback_query(StateFilter(ProfileStates.BROWSING), F.data.startswith("dislike_"))
async def on_dislike(callback: types.CallbackQuery, state: FSMContext):
    # Пользователь пропустил анкету
    await show_next_profile(callback)

@router.callback_query(StateFilter(ProfileStates.BROWSING), F.data == "exit_browse")
async def on_exit_browse(callback: types.CallbackQuery, state: FSMContext):
    # Выйти из режима просмотра
    await callback.message.delete()  # удаляем последнюю показанную анкету
    await state.set_state(ProfileStates.MENU)
    await callback.message.answer("Вы вернулись в меню.", reply_markup=build_menu_keyboard())
