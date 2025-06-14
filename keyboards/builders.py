from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def build_gender_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Парень"), KeyboardButton(text="Девушка")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def build_preference_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Парни"), KeyboardButton(text="Девушки")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def build_confirmation_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Верно")],
            [KeyboardButton(text="🔄 Заполнить заново")]
        ],
        resize_keyboard=True
    )

# Add this new function
def build_location_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Поделиться локацией", request_location=True)],
            [KeyboardButton(text="🚫 Продолжить без локации")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )