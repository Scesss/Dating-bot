from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def gender_choice():
    buttons = [[
        InlineKeyboardButton(text="Мужчина", callback_data="gender:Мужчина"),
        InlineKeyboardButton(text="Женщина", callback_data="gender:Женщина"),
    ]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def preference_choice():
    buttons = [[
        InlineKeyboardButton(text="Мужчина", callback_data="pref:Мужчина"),
        InlineKeyboardButton(text="Женщина", callback_data="pref:Женщина"),
        InlineKeyboardButton(text="Любой",    callback_data="pref:Любой"),
    ]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def browse_buttons(target_user_id):
    buttons = [[
        InlineKeyboardButton(text="👍 Нравится", callback_data=f"like:{target_user_id}"),
        InlineKeyboardButton(text="👎 Далее",    callback_data=f"skip:{target_user_id}"),
    ]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def edit_menu():
    buttons = [
        [
            InlineKeyboardButton(text="✏️ Имя",           callback_data="edit:name"),
            InlineKeyboardButton(text="👤 Пол",           callback_data="edit:gender"),
        ],
        [
            InlineKeyboardButton(text="📝 О себе",       callback_data="edit:about"),
            InlineKeyboardButton(text="🎂 Возраст",      callback_data="edit:age"),
        ],
        [
            InlineKeyboardButton(text="🏙 Город",        callback_data="edit:city"),
            InlineKeyboardButton(text="❤️ Предпочтения", callback_data="edit:preference"),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
