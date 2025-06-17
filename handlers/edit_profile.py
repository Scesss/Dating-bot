from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards.builders import get_edit_menu_kb, get_params_menu_kb
from states.profile_states import ProfileStates
from aiogram.filters import StateFilter
from database import db
from keyboards.builders import build_menu_keyboard, build_cancel_keyboard


router = Router()

def generate_profile_caption(profile: dict) -> str:
    """
    Собирает и возвращает строку с данными профиля:
    - имя, возраст, пол
    - кого ищет, город (или 'Не указан')
    - текст 'О себе' (обрезанный до 1000 символов)
    """
    return (
        f"Имя: {profile.get('name', 'N/A')}\n"
        f"Возраст: {profile.get('age', 'N/A')}\n"
        f"Пол: {profile.get('gender', 'N/A')}\n"
        f"Ищет: {profile.get('looking_for', 'N/A')}\n"
        f"Город: {profile.get('city') or 'Не указан'}\n"
        f"О себе: {(profile.get('bio') or '')[:1000]}"
    )



# @router.message(StateFilter(ProfileStates.EDIT_PROFILE))
# async def cmd_edit(message: types.Message, state: FSMContext):
#     await message.answer(
#         "Выберите действие:",
#         reply_markup=get_edit_menu_kb()
#     )

@router.callback_query(F.data == "cancel_edit", StateFilter(ProfileStates.EDIT_PROFILE))
async def on_cancel_edit(callback: types.CallbackQuery, state: FSMContext):
    # Отмена редактирования: удалить сообщение анкеты и вернуть в меню
    await callback.message.delete()
    await state.set_state(ProfileStates.MENU)
    await callback.message.answer("Вы вернулись в главное меню.", reply_markup=build_menu_keyboard())
    await callback.answer()



@router.callback_query(F.data == "refill_profile", StateFilter(ProfileStates.EDIT_PROFILE))
async def on_refill_profile(callback: types.CallbackQuery, state: FSMContext):
    # Удаляем сообщение с профилем
    await callback.message.delete()
    # Очищаем состояние и запускаем регистрацию заново
    await state.clear()
    await callback.message.answer("Начнём заполнение анкеты с начала. Как тебя зовут?", reply_markup=build_cancel_keyboard())
    await state.set_state(ProfileStates.NAME)
    await callback.answer()



@router.callback_query(F.data == "edit_params", StateFilter(ProfileStates.EDIT_PROFILE))
async def on_edit_params(callback: types.CallbackQuery):
    # Меняем inline-клавиатуру сообщения профиля на список параметров
    await callback.message.edit_reply_markup(reply_markup=get_params_menu_kb())
    await callback.answer()  # убираем "часики" на кнопке

@router.callback_query(F.data == "back_to_edit_menu", StateFilter(ProfileStates.EDIT_PROFILE))
async def on_back_to_edit_menu(callback: types.CallbackQuery):
    # Возвращаем основное меню действий (редактировать/заполнить/назад)
    await callback.message.edit_reply_markup(reply_markup=get_edit_menu_kb())
    await callback.answer()

# @router.callback_query(F.data == "edit_name", StateFilter(ProfileStates.EDIT_PROFILE))
# async def on_edit_name(callback: types.CallbackQuery, state: FSMContext):
#     # Убрать клавиатуру с профиля, чтобы не нажимали параллельно
#     await callback.message.edit_reply_markup(reply_markup=None)
#     # Спросить новое имя
#     await callback.message.answer("Введите новое имя:", reply_markup=build_cancel_keyboard())
#     await state.set_state(ProfileStates.EDIT_NAME)
#     await callback.answer()

# @router.message(StateFilter(ProfileStates.EDIT_NAME))
# async def process_edit_name(message: types.Message, state: FSMContext):
#     if message.text == "🚫 Отмена":
#         # Отменяем изменение имени, возвращаемся к просмотру профиля
#         profile = db.get_profile(message.from_user.id)
#         if profile:
#             # Показываем актуальный профиль снова
#             await message.answer("Изменение отменено.", reply_markup=types.ReplyKeyboardRemove())
#             await message.answer_photo(profile['photo_id'],
#                                        caption=generate_profile_caption(profile),
#                                        reply_markup=get_edit_menu_kb())
#         await state.set_state(ProfileStates.EDIT_PROFILE)
#         return
#     # Проверка длины имени
#     if len(message.text.strip()) < 2:
#         await message.answer("Имя не может быть короче двух букв. Попробуйте снова:")
#         return
#     # Обновляем имя в БД
#     db.update_profile_field(message.from_user.id, 'name', message.text.strip())
#     # Сообщаем об успешном обновлении
#     await message.answer("Имя обновлено.", reply_markup=types.ReplyKeyboardRemove())
#     # Получаем обновлённый профиль и показываем снова
#     profile = db.get_profile(message.from_user.id)
#     if profile:
#         await message.answer_photo(profile['photo_id'],
#                                    caption=generate_profile_caption(profile),
#                                    reply_markup=get_edit_menu_kb())
#     await state.set_state(ProfileStates.EDIT_PROFILE)

@router.callback_query(F.data == "edit_age", StateFilter(ProfileStates.EDIT_PROFILE))
async def on_edit_age(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Введите новый возраст:", reply_markup=build_cancel_keyboard())
    await state.set_state(ProfileStates.EDIT_AGE)
    await callback.answer()

@router.message(StateFilter(ProfileStates.EDIT_AGE))
async def process_edit_age(message: types.Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        # Отмена изменения – вернуть профиль
        profile = db.get_profile(message.from_user.id)
        if profile:
            await message.answer("Изменение отменено.", reply_markup=types.ReplyKeyboardRemove())
            await message.answer_photo(profile['photo_id'],
                                       caption=generate_profile_caption(profile),
                                       reply_markup=get_edit_menu_kb())
        await state.set_state(ProfileStates.EDIT_PROFILE)
        return
    if not message.text.isdigit():
        await message.answer("Возраст должен быть числом. Попробуйте снова:")
        return
    age = int(message.text)
    if age < 14 or age > 100:
        await message.answer("Укажите корректный возраст (14-100).")
        return
    db.update_profile_field(message.from_user.id, 'age', age)
    await message.answer("Возраст обновлен.", reply_markup=types.ReplyKeyboardRemove())
    profile = db.get_profile(message.from_user.id)
    if profile:
        await message.answer_photo(profile['photo_id'],
                                   caption=generate_profile_caption(profile),
                                   reply_markup=get_edit_menu_kb())
    await state.set_state(ProfileStates.EDIT_PROFILE)


@router.callback_query(F.data == "edit_bio", StateFilter(ProfileStates.EDIT_PROFILE))
async def on_edit_bio(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Напишите новый текст 'О себе':", reply_markup=build_cancel_keyboard())
    await state.set_state(ProfileStates.EDIT_BIO)
    await callback.answer()

@router.message(StateFilter(ProfileStates.EDIT_BIO))
async def process_edit_bio(message: types.Message, state: FSMContext):
    if message.text == "🚫 Отмена":
        profile = db.get_profile(message.from_user.id)
        if profile:
            await message.answer("Изменение отменено.", reply_markup=types.ReplyKeyboardRemove())
            await message.answer_photo(profile['photo_id'],
                                       caption=generate_profile_caption(profile),
                                       reply_markup=get_edit_menu_kb())
        await state.set_state(ProfileStates.EDIT_PROFILE)
        return
    bio_text = message.text.strip()
    if len(bio_text) > 1000:
        await message.answer("Слишком длинный текст. Максимум 1000 символов.")
        return
    db.update_profile_field(message.from_user.id, 'bio', bio_text)
    await message.answer("Описание обновлено.", reply_markup=types.ReplyKeyboardRemove())
    profile = db.get_profile(message.from_user.id)
    if profile:
        await message.answer_photo(profile['photo_id'],
                                   caption=generate_profile_caption(profile),
                                   reply_markup=get_edit_menu_kb())
    await state.set_state(ProfileStates.EDIT_PROFILE)



@router.callback_query(F.data == "edit_photo", StateFilter(ProfileStates.EDIT_PROFILE))
async def on_edit_photo(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Отправьте новое фото профиля:", reply_markup=build_cancel_keyboard())
    await state.set_state(ProfileStates.EDIT_PHOTO)
    await callback.answer()

@router.message(StateFilter(ProfileStates.EDIT_PHOTO), F.photo)
async def process_edit_photo(message: types.Message, state: FSMContext):
    # Берём последнее фото из списка (наивысшее качество)
    photo = message.photo[-1]
    new_file_id = photo.file_id
    db.update_profile_field(message.from_user.id, 'photo_id', new_file_id)
    await message.answer("Фото обновлено.", reply_markup=types.ReplyKeyboardRemove())
    profile = db.get_profile(message.from_user.id)
    if profile:
        await message.answer_photo(profile['photo_id'],
                                   caption=generate_profile_caption(profile),
                                   reply_markup=get_edit_menu_kb())
    await state.set_state(ProfileStates.EDIT_PROFILE)



# @router.callback_query(F.data == "edit_geo", StateFilter(ProfileStates.EDIT_PROFILE))
# async def edit_geo(callback: types.CallbackQuery, state: FSMContext):
#     await callback.answer()
