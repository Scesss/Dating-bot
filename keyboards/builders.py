from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def build_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Смотреть Анкеты")],
            [KeyboardButton(text="Моя Анкета")],
            [KeyboardButton(text="Топ"), KeyboardButton(text="Сон")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def build_gender_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Парень"), KeyboardButton(text="Девушка")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def build_preference_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Парни"), KeyboardButton(text="Девушки")],
            [KeyboardButton(text="⬅️ Назад")]
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
            [KeyboardButton(text="📍 Поделиться местоположением", request_location=True)],
            # [KeyboardButton(text="✏️ Ввести город вручную")],
            [KeyboardButton(text="🚫 Пропустить")],
            [KeyboardButton(text="⬅️ Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def build_back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⬅️ Назад")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def build_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚫 Отмена")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )