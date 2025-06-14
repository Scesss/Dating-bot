from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from states.profile_states import ProfileStates
from keyboards.builders import (build_gender_keyboard, build_preference_keyboard,
                                build_confirmation_keyboard, build_location_keyboard)
from aiogram.filters import StateFilter
from services.geocoding import get_city_name
from aiogram.filters import Command


router = Router()

# Handle name
@router.message(StateFilter(ProfileStates.NAME))
async def process_name(message: types.Message, state: FSMContext):
    if len(message.text) < 2:
        return await message.answer("Имя не может быть короче двух букв")
    await state.update_data(name=message.text)
    await message.answer("Сколько тебе лет?")
    await state.set_state(ProfileStates.AGE)


# Handle age
@router.message(StateFilter(ProfileStates.AGE))
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Возраст должен быть целым числом.")

    age = int(message.text)
    if age < 14 or age > 100:
        return await message.answer("Введите корректный возраст.")

    await state.update_data(age=age)
    await message.answer(
        "Твой пол?",
        reply_markup=build_gender_keyboard()
    )
    await state.set_state(ProfileStates.GENDER)


# Handle gender
@router.message(StateFilter(ProfileStates.GENDER))
async def process_gender(message: types.Message, state: FSMContext):
    valid_genders = ["Парень", "Девушка"]
    if message.text not in valid_genders:
        return await message.answer("Нет такого варианта ответа")

    await state.update_data(gender=message.text)
    await message.answer(
        "Кто тебе интересен?",
        reply_markup=build_preference_keyboard()
    )
    await state.set_state(ProfileStates.LOOKING_FOR)


# Handle preference
@router.message(StateFilter(ProfileStates.LOOKING_FOR))
async def process_preference(message: types.Message, state: FSMContext):
    valid_options = ["Девушки", "Парни"]
    if message.text not in valid_options:
        return await message.answer("Нет такого варианта ответа")

    await state.update_data(looking_for=message.text)
    await message.answer(
        "Расскажи о себе:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(ProfileStates.BIO)


# Handle bio
@router.message(StateFilter(ProfileStates.BIO))
async def process_bio(message: types.Message, state: FSMContext):
    # if len(message.text) < 50:
    #     return await message.answer("Your bio should be at least 50 characters. Try again:")
    #
    if len(message.text) > 1000:
        return await message.answer("Ваше сообщение не должно быть длиннее 1000 символов.")

    await state.update_data(bio=message.text)
    await message.answer("Твое фото?")
    await state.set_state(ProfileStates.PHOTO)



# Handle photo
@router.message(StateFilter(ProfileStates.PHOTO, F.photo))
async def process_photo(message: types.Message, state: FSMContext):
    # Get highest resolution photo
    photo = message.photo[-1]
    await state.update_data(photo_id=photo.file_id)

    await message.answer(
        "Отправь мне свою геопозицию:",
        reply_markup=build_location_keyboard()
    )
    await state.set_state(ProfileStates.LOCATION)


# Handle invalid photo
@router.message(StateFilter(ProfileStates.PHOTO))
async def process_photo_invalid(message: types.Message):
    await message.answer("Требуется фото.")


# Remove the old LOCATION handler and replace with this:
@router.message(ProfileStates.LOCATION)
async def process_location(message: types.Message, state: FSMContext):
    location_data = None

    if message.location:
        # User shared location via button
        lat = message.location.latitude
        lon = message.location.longitude
        location_data = f"{lat},{lon}"
        await state.update_data(location=location_data)
        await message.answer("📍 Локация получена! Спасибо")
    elif message.text and message.text == "🚫 Продолжить без локации":
        # User chose to skip
        await state.update_data(location=None)
        await message.answer("Геолокация не будет использоваться при поиске")
    else:
        # Invalid input
        await message.answer("Ошибка, используйте кнопки снизу")
        return  # Stay in current state


    # Prepare confirmation
    data = await state.get_data()

    city_name = "Не указан"
    if data.get('location'):
        try:
            lat, lon = map(float, data['location'].split(','))
            city_name = await get_city_name(lat, lon)
        except Exception as e:
            # logger.error(f"Failed to get city name: {e}")
            city_name = "Неизвестный город"

    confirmation_text = (
        "📝 Подтвердите данные вашего профиля:\n\n"
        f"👤 Имя: {data.get('name', 'N/A')}\n"
        f"🎂 Возраст: {data.get('age', 'N/A')}\n"
        f"🚻 Пол: {data.get('gender', 'N/A')}\n"
        f"💘 Ищу: {data.get('looking_for', 'N/A')}\n"
        f"🌎: {city_name}\n"  # Show city name here
        f"📖 О себе: {data.get('bio', 'N/A')[:500]}\n"
        "Все верно?"
    )

    if 'photo_id' in data:
        await message.answer_photo(
            photo=data['photo_id'],
            caption=confirmation_text,
            reply_markup=build_confirmation_keyboard()
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
        # Save profile to database (we'll implement this later)
        data = await state.get_data()
        await message.answer(
            "Профиль сохранен успешно! 🎉\n",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.clear()
    elif message.text == "🔄 Заполнить заново":
        await state.clear()
        await message.answer(
            "Profile creation restarted. Type /start to begin again.",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await message.answer("Нет такого варианта ответа")



__all__ = ['router']