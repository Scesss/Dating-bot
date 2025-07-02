from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
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
            text="◀️ Назад",
            callback_data="back_to_edit_menu"
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

    return builder.as_markup()

def build_menu_keyboard(user_gender: str):
    profile_label = "👨🏼 Моя Анкета" if user_gender == "Парень" else "👩🏻‍🦰 Моя Анкета"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Смотреть Анкеты")],
            [KeyboardButton(text=profile_label)],
            [KeyboardButton(text="👑 Топ"), KeyboardButton(text="🌙 Сон")]
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

def build_restart_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚫 Отмена")],
                  [KeyboardButton(text="✅ Вперед")]
                  ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_browse_keyboard(target_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👍 Лайк",              callback_data=f"like_simple:{target_id}"),
            InlineKeyboardButton(text="💬 Лайк с сообщением", callback_data=f"like_msg:{target_id}"),
            InlineKeyboardButton(text="💰 Лайк с чеком",      callback_data=f"like_cash:{target_id}")
        ],
        [
            InlineKeyboardButton(text="👎 Дизлайк",           callback_data=f"dislike:{target_id}"),
            InlineKeyboardButton(text="📖 Завершить просмотр", callback_data="exit_browse")
        ]
    ])
def build_match_keyboard(user_id):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="💌️ Написать этому человеку",
            url=f"tg://user?id={user_id}"
        )],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="matches_prev"),
         InlineKeyboardButton(text="▶️ Вперёд", callback_data="matches_next")],
        [InlineKeyboardButton(text="◀ Завершить просмотр", callback_data="exit_matches")]
    ])
    return kb



def build_top_navigation_keyboard(
    current_index: int,
    total: int
) -> InlineKeyboardMarkup:
    """
    Возвращает:
      – Для первого профиля: [❌ Главное меню] [➡️]
      – Для последнего:      [❌ Главное меню] [⬅️]
      – Для остальных:       [⬅️] [❌ Главное меню] [➡️]
    И внизу всегда ряд со статусом “текущая/всего”.
    """

    if current_index == 0:
        # первый профиль — показываем только «вперёд»
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬇️",            callback_data="top:next")],
            [InlineKeyboardButton(text="◀ Завершить просмотр", callback_data="top:exit")]
        ])

    elif current_index == total - 1:
        # последний профиль — показываем только «назад»
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬆️", callback_data="top:prev")],
            [InlineKeyboardButton(text="◀ Завершить просмотр", callback_data="top:exit")]
        ])

    else:
        # любой профиль между первым и последним
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬆️", callback_data="top:prev")],
            [InlineKeyboardButton(text="⬇️", callback_data="top:next")],
            [InlineKeyboardButton(text="◀ Завершить просмотр", callback_data="top:exit")]
        ])

    # строка статуса: “1/10”, “2/10” и т.д.
    # kb.row(
    #     InlineKeyboardButton(text=f"{current_index + 1}/{total}", callback_data="ignore")
    # )

    return kb
