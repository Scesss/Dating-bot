from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from states.profile_states import ProfileStates
from keyboards.builders import build_gender_keyboard, build_preference_keyboard, build_confirmation_keyboard
from aiogram.filters import StateFilter
from aiogram.filters import Command


router = Router()

# @router.message()
# async def

# @router.message(Command("start"))
# async def cmd_start(message: types.Message, state: FSMContext):
#     await state.clear()
#     await message.answer(
#         "🌟 Welcome to Dating Bot! Let's create your profile.\n"
#         "Type /profile to get started."
#     )
#
#
# @router.message(Command("profile"))
# async def start_profile(message: types.Message, state: FSMContext):
#     current_state = await state.get_state()
#     print(f"Current state: {current_state}")
#     await state.set_state(ProfileStates.NAME)
#     await message.answer("Let's create your profile! What's your name?")


# Start questionnaire



# Handle name
@router.message(StateFilter(ProfileStates.NAME))
async def process_name(message: types.Message, state: FSMContext):
    if len(message.text) < 2:
        return await message.answer("Name should be at least 2 characters. Try again:")
    await state.update_data(name=message.text)
    await message.answer("Great! Now how old are you?")
    await state.set_state(ProfileStates.AGE)


# Handle age
@router.message(StateFilter(ProfileStates.AGE))
async def process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Please enter a valid age (numbers only)")

    age = int(message.text)
    if age < 18 or age > 100:
        return await message.answer("Please enter a valid age (18-100)")

    await state.update_data(age=age)
    await message.answer(
        "What's your gender?",
        reply_markup=build_gender_keyboard()
    )
    await state.set_state(ProfileStates.GENDER)


# Handle gender
@router.message(StateFilter(ProfileStates.GENDER))
async def process_gender(message: types.Message, state: FSMContext):
    valid_genders = ["Male", "Female", "Non-binary", "Prefer not to say"]
    if message.text not in valid_genders:
        return await message.answer("Please choose a valid option from the keyboard.")

    await state.update_data(gender=message.text)
    await message.answer(
        "What gender are you interested in?",
        reply_markup=build_preference_keyboard()
    )
    await state.set_state(ProfileStates.LOOKING_FOR)


# Handle preference
@router.message(StateFilter(ProfileStates.LOOKING_FOR))
async def process_preference(message: types.Message, state: FSMContext):
    valid_options = ["Men", "Women", "Anyone", "Non-binary only"]
    if message.text not in valid_options:
        return await message.answer("Please choose a valid option from the keyboard.")

    await state.update_data(looking_for=message.text)
    await message.answer(
        "Tell us about yourself in a short bio (min 50 characters):",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(ProfileStates.BIO)


# Handle bio
@router.message(StateFilter(ProfileStates.BIO))
async def process_bio(message: types.Message, state: FSMContext):
    if len(message.text) < 50:
        return await message.answer("Your bio should be at least 50 characters. Try again:")

    if len(message.text) > 500:
        return await message.answer("Your bio is too long! Max 500 characters.")

    await state.update_data(bio=message.text)
    await message.answer("What are your main interests? (Separate with commas)")
    await state.set_state(ProfileStates.INTERESTS)


# Handle interests
@router.message(StateFilter(ProfileStates.INTERESTS))
async def process_interests(message: types.Message, state: FSMContext):
    interests = [i.strip() for i in message.text.split(",") if i.strip()]
    if len(interests) < 2:
        return await message.answer("Please enter at least 2 interests separated by commas.")

    await state.update_data(interests=",".join(interests))
    await message.answer("Please send your profile photo:")
    await state.set_state(ProfileStates.PHOTO)


# Handle photo
@router.message(StateFilter(ProfileStates.PHOTO, F.photo))
async def process_photo(message: types.Message, state: FSMContext):
    # Get highest resolution photo
    photo = message.photo[-1]
    await state.update_data(photo_id=photo.file_id)

    await message.answer("What city are you located in? (Just the city name)")
    await state.set_state(ProfileStates.LOCATION)


# Handle invalid photo
@router.message(StateFilter(ProfileStates.PHOTO))
async def process_photo_invalid(message: types.Message):
    await message.answer("Please send a valid photo.")


# Handle location
@router.message(StateFilter(ProfileStates.LOCATION))
async def process_location(message: types.Message, state: FSMContext):
    if len(message.text) < 2:
        return await message.answer("Please enter a valid city name.")

    await state.update_data(location=message.text)

    # Prepare confirmation
    data = await state.get_data()
    confirmation_text = (
        "📝 Please confirm your profile:\n\n"
        f"👤 Name: {data.get('name', 'N/A')}\n"
        f"🎂 Age: {data.get('age', 'N/A')}\n"
        f"🚻 Gender: {data.get('gender', 'N/A')}\n"
        f"💘 Looking for: {data.get('looking_for', 'N/A')}\n"
        f"📍 Location: {data.get('location', 'N/A')}\n"
        f"📖 Bio: {data.get('bio', 'N/A')[:100]}...\n"
        f"🎯 Interests: {data.get('interests', 'N/A')}\n\n"
        "Is this information correct?"
    )

    # Show photo preview
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


# Handle confirmation
@router.message(StateFilter(ProfileStates.CONFIRMATION))
async def process_confirmation(message: types.Message, state: FSMContext):
    if message.text == "✅ Confirm":
        # Save profile to database (we'll implement this later)
        data = await state.get_data()
        await message.answer(
            "Profile saved successfully! 🎉\nUse /matches to see potential matches.",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.clear()
    elif message.text == "🔄 Restart":
        await state.clear()
        await message.answer(
            "Profile creation restarted. Type /start to begin again.",
            reply_markup=types.ReplyKeyboardRemove()
        )
    else:
        await message.answer("Please choose an option using the buttons.")

__all__ = ['router']