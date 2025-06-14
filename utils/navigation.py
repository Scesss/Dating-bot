from aiogram.fsm.context import FSMContext
from states.profile_states import ProfileStates
from keyboards.builders import *

class Navigation:
    # Define the order of registration steps
    STEP_ORDER = [
        ProfileStates.NAME,
        ProfileStates.AGE,
        ProfileStates.GENDER,
        ProfileStates.LOOKING_FOR,
        ProfileStates.BIO,
        ProfileStates.PHOTO,
        ProfileStates.LOCATION,
        ProfileStates.CONFIRMATION
    ]

    @classmethod
    def get_previous_step(cls, current_state):
        """Get the previous step in the registration flow"""
        try:
            index = cls.STEP_ORDER.index(current_state)
            return cls.STEP_ORDER[index - 1] if index > 0 else None
        except ValueError:
            return None

    @classmethod
    async def go_back(cls, message, state: FSMContext):
        """Navigate to previous step and resend its prompt"""
        current_state = await state.get_state()
        previous_state = cls.get_previous_step(current_state)

        if previous_state:
            await state.set_state(previous_state)
            await cls.send_step_prompt(message, state, previous_state)
            return True
        return False

    @classmethod
    async def send_step_prompt(cls, message, state: FSMContext, target_state):
        """Resend the appropriate prompt for a registration step"""
        # Get current data to pre-fill if available
        data = await state.get_data()

        if target_state == ProfileStates.NAME:
            await message.answer(
                "Введите ваше имя:",
                reply_markup=build_cancel_keyboard()
            )

        elif target_state == ProfileStates.AGE:
            name = data.get('name', '')
            await message.answer(
                "Сколько тебе лет?",
                reply_markup=build_back_keyboard()
            )

        elif target_state == ProfileStates.GENDER:
            await message.answer(
                "Выберите ваш пол:",
                reply_markup=build_gender_keyboard()
            )

        elif target_state == ProfileStates.LOOKING_FOR:
            await message.answer(
                "Кто тебе интересен?",
                reply_markup=build_preference_keyboard()
            )

        elif target_state == ProfileStates.LOCATION:
            await message.answer(
                "Поделитесь местоположением:",
                reply_markup=build_location_keyboard()
            )

        elif target_state == ProfileStates.BIO:
            await message.answer(
                "Расскажи о себе:",
                reply_markup=build_back_keyboard()
            )

        elif target_state == ProfileStates.PHOTO:
            await message.answer(
                "Твое фото?",
                reply_markup=build_back_keyboard()
            )

    # Add similar keyboard builders for other states...