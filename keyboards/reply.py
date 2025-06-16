from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    keyboard = [
        [KeyboardButton(text="👤 Моя анкета")],
        [KeyboardButton(text="🔍 Просмотр анкет")],
        [KeyboardButton(text="💛 Кто меня лайкнул")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
