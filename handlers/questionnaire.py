from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from handlers.common import cmd_start
from states.profile_states import ProfileStates
from keyboards.builders import *
from aiogram.filters import StateFilter
from services.geocoding import get_city_name, is_valid_city
from utils.navigation import Navigation
from database import db
import logging
from aiogram.filters import Command
from services.geocoding import get_city_name_from_query

logger = logging.getLogger(__name__)
router = Router()

# Handle name


@router.message(StateFilter(ProfileStates.NAME))
async def process_name(message: types.Message, state: FSMContext, bot : Bot):
    if message.text == "🚫 Отмена":
        await cmd_start(message, state, bot)
        return

    if len(message.text) < 2:
        return await message.answer("❌ Имя не может быть короче двух букв")
    await state.update_data(name=message.text)
    await message.answer("❔ Сколько тебе лет?", reply_markup=build_back_keyboard())
    await state.set_state(ProfileStates.AGE)


# Handle age
@router.message(StateFilter(ProfileStates.AGE))
async def process_age(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await Navigation.go_back(message, state)
        return

    if not message.text.isdigit():
        return await message.answer("❌ Возраст должен быть целым числом.")

    age = int(message.text)
    if age < 14 or age > 100:
        return await message.answer("❌ Введите корректный возраст.")

    await state.update_data(age=age)
    await message.answer(
        "👤 Твой пол?",
        reply_markup=build_gender_keyboard()
    )
    await state.set_state(ProfileStates.GENDER)


# Handle gender
@router.message(StateFilter(ProfileStates.GENDER))
async def process_gender(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await Navigation.go_back(message, state)
        return

    valid_genders = ["Парень", "Девушка"]
    if message.text not in valid_genders:
        return await message.answer("❌ Нет такого варианта ответа")

    await state.update_data(gender=message.text)
    await message.answer(
        "💕 Кто тебе интересен?",
        reply_markup=build_preference_keyboard()
    )
    await state.set_state(ProfileStates.LOOKING_FOR)


# Handle preference
@router.message(StateFilter(ProfileStates.LOOKING_FOR))
async def process_preference(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await Navigation.go_back(message, state)
        return

    valid_options = ["Девушки", "Парни"]
    if message.text not in valid_options:
        return await message.answer("❌ Нет такого варианта ответа")

    await state.update_data(looking_for=message.text)
    await message.answer(
        "✍️ Расскажи о себе:",
        reply_markup=build_back_keyboard()
    )
    await state.set_state(ProfileStates.BIO)


# Handle bio
@router.message(StateFilter(ProfileStates.BIO))
async def process_bio(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await Navigation.go_back(message, state)
        return

    # if len(message.text) < 50:
    #     return await message.answer("Your bio should be at least 50 characters. Try again:")
    #
    if len(message.text) > 1000:
        return await message.answer("❌ Ваше сообщение не должно быть длиннее 1000 символов.")

    await state.update_data(bio=message.text)
    await message.answer("📸 Твое фото?", reply_markup=build_back_keyboard())
    await state.set_state(ProfileStates.PHOTO)



# Handle photo
@router.message(StateFilter(ProfileStates.PHOTO, F.photo))
async def process_photo(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await Navigation.go_back(message, state)
        return

    # Get highest resolution photo
    photo = message.photo[-1]
    await state.update_data(photo_id=photo.file_id)

    await message.answer(
        "📍 Из какого ты города?",
        reply_markup=build_location_keyboard()
    )
    await state.set_state(ProfileStates.LOCATION)


# Handle invalid photo
@router.message(StateFilter(ProfileStates.PHOTO))
async def process_photo_invalid(message: types.Message):
    await message.answer("❌ Требуется фото.")

# @router.message(ProfileStates.LOCATION,F.text == "✏️ Ввести город вручную")
# async def request_city_input(message: types.Message):
#     await message.answer(
#         "Пожалуйста, введите название вашего города:",
#         reply_markup=types.ReplyKeyboardRemove()
#     )

# Remove the old LOCATION handler and replace with this:
@router.message(ProfileStates.LOCATION)
async def process_location(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await Navigation.go_back(message, state)
        return

    location_data = None
    city_name = None

    # Handle location sharing via button
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        location_data = f"{lat},{lon}"
        city_name = await get_city_name(lat, lon)
        await message.answer(f"✅ Местоположение получено: {city_name}")

    # Handle skip location
    elif message.text and message.text == "🚫 Пропустить":
        await message.answer("Определение местоположения пропущено, рекомендации могут быть менее точными...")

    elif message.text:
        # сначала проверяем, что это вообще город
        ok = await is_valid_city(message.text)
        if not ok:
            await message.answer(
                "❌ Не удалось распознать город. Попробуйте, например, «Москва» или "
                "отправьте геолокацию через кнопку."
            )
            return

        # получаем каноническое название из геокодера
        canon = await get_city_name_from_query(message.text)
        if canon:
            city_name = canon
        else:
            # на случай, если что-то пошло не так — всё равно сохраним user input
            city_name = message.text.title()

        await message.answer(f"✅ Город сохранён: {city_name}")

    else:
        # Invalid input
        await message.answer("❌ Пожалуйста, используйте кнопки ниже или введите корректное название города.")
        return

    # Update state data
    await state.update_data({
        "location": location_data,
        "city_name": city_name  # Store both coordinates and city name
    })

    # Proceed to confirmation
    await show_confirmation(message, state)


async def show_confirmation(message: types.Message, state: FSMContext):
    data = await state.get_data()

    # Prepare confirmation text
    confirmation_text = (
        "📝 Пожалуйста, подтвердите ваш профиль:\n\n"
        f"👤 Имя: {data.get('name', 'Н/Д')}\n"
        f"🎂 Возраст: {data.get('age', 'Н/Д')}\n"
        f"🚻 Пол: {data.get('gender', 'Н/Д')}\n"
        f"💘 Ищу: {data.get('looking_for', 'Н/Д')}\n"
        f"📍 Город: {data.get('city_name', 'Не указан')}\n"
        f"📖 О себе: {data.get('bio', 'Н/Д')[:100]}...\n"
        "Всё верно?"
    )

    # Show profile photo if available
    if 'photo_id' in data:
        await message.answer_photo(
            photo=data['photo_id'],
            caption=confirmation_text,
            reply_markup=build_confirmation_keyboard(),
            parse_mode  = None
        )
    else:
        await message.answer(
            confirmation_text,
            reply_markup=build_confirmation_keyboard()
        )

    await state.set_state(ProfileStates.CONFIRMATION)


@router.message(ProfileStates.CONFIRMATION)
async def process_confirmation(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if message.text == "✅ Верно":
        # Сохранение профиля в базу данных
        try:
            db.save_profile(
                user_id=message.from_user.id,
                name=data.get('name'),
                age=data.get('age'),
                gender=data.get('gender'),
                looking_for=data.get('looking_for'),
                bio=data.get('bio'),
                photo_id=data.get('photo_id'),
                city=data.get('city_name'),              # название города (может быть None)
                # координаты храним как числовые поля; распарсим строку "lat,lon", если есть
                lat=float(data['location'].split(',')[0]) if data.get('location') else None,
                lon=float(data['location'].split(',')[1]) if data.get('location') else None
            )

        except Exception as e:
            logging.error(f"Error saving profile: {e}")

        # await message.answer(
        #     "Профиль сохранён успешно! 🎉",
        #     reply_markup=types.ReplyKeyboardRemove()
        # )
        # await state.clear()
        await message.answer("Профиль сохранён успешно! 🎉", reply_markup=build_menu_keyboard(data["gender"]))
        await state.set_state(ProfileStates.MENU)


        # После сохранения можно показать меню / профиль пользователю,
        # например, отправить приветствие или сразу вызвать /start.
        # (В данном случае мы просто очистили состояние и убрали клавиатуру.)
    elif message.text == "🔄 Заполнить заново":
        await message.answer(" Начнём заполнение анкеты с начала. Как тебя зовут?", reply_markup=build_cancel_keyboard())
        await state.set_state(ProfileStates.NAME)

@router.message(ProfileStates.RESTART)
async def process_restart(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if message.text == "✅ Вперед":
        await message.answer("❔ Начнём заполнение анкеты. Как тебя зовут?",
                             reply_markup=build_cancel_keyboard())
        await state.set_state(ProfileStates.NAME)
    else:
        profile = db.get_profile(message.from_user.id)
        gender = profile.get("gender")
        await message.answer("⏳ Возвращаемся в меню...",
                             reply_markup=build_menu_keyboard(gender))





__all__ = ['router']