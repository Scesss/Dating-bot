from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types

# Клавиатура главного меню редактирования
def get_edit_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="cancel_edit"
        ),
        types.InlineKeyboardButton(
            text="🔄 Заполнить заново",
            callback_data="refill_profile"
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="✏️ Редактировать параметры",
            callback_data="edit_params"
        )
    )
    return builder.as_markup()

# Клавиатура выбора параметров для редактирования
def get_params_menu_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(
            text="👤 Имя",
            callback_data="edit_name"
        ),
        types.InlineKeyboardButton(
            text="🔢 Возраст",
            callback_data="edit_age"
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="📝 Bio",
            callback_data="edit_bio"
        ),
        types.InlineKeyboardButton(
            text="🖼 Фото",
            callback_data="edit_photo"
        )
    )
    builder.row(
        types.InlineKeyboardButton(
            text="📍 Гео",
            callback_data="edit_geo"
        ),
        types.InlineKeyboardButton(
            text="◀️ Назад",
            callback_data="back_to_edit_menu"
        )
    )
    return builder.as_markup()

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