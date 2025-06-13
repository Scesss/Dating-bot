from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def build_gender_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Male"), KeyboardButton(text="Female")],
            [KeyboardButton(text="Non-binary"), KeyboardButton(text="Prefer not to say")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def build_preference_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Men"), KeyboardButton(text="Women")],
            [KeyboardButton(text="Anyone"), KeyboardButton(text="Non-binary only")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def build_confirmation_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Confirm")],
            [KeyboardButton(text="🔄 Restart")]
        ],
        resize_keyboard=True
    )