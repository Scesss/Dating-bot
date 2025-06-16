from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from fsm.states import ProfileForm
from keyboards.inline import gender_choice, preference_choice
from keyboards.reply import main_menu
from database.db import save_profile

router = Router()

@router.message(lambda message: message.text == "/start")
async def start_profile(message: Message, state: FSMContext):
    await message.answer("Введите ваше имя:", reply_markup=None)
    await state.set_state(ProfileForm.name)

@router.message(ProfileForm.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Выберите ваш пол:", reply_markup=gender_choice())
    await state.set_state(ProfileForm.gender)

@router.callback_query(F.data.startswith("gender:"))
async def process_gender(call: CallbackQuery, state: FSMContext):
    gender = call.data.split(":",1)[1]
    await state.update_data(gender=gender)
    await call.message.answer("Расскажите немного о себе:", reply_markup=None)
    await state.set_state(ProfileForm.about)
    await call.answer()

@router.message(ProfileForm.about)
async def process_about(message: Message, state: FSMContext):
    await state.update_data(about=message.text.strip())
    await message.answer("Укажите ваш возраст (числом):", reply_markup=None)
    await state.set_state(ProfileForm.age)

@router.message(ProfileForm.age)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите число.")
        return
    await state.update_data(age=int(message.text))
    await message.answer("Укажите ваш город:", reply_markup=None)
    await state.set_state(ProfileForm.city)

@router.message(ProfileForm.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text.strip())
    await message.answer("Кого вы ищете?", reply_markup=preference_choice())
    await state.set_state(ProfileForm.preference)

@router.callback_query(F.data.startswith("pref:"))
async def process_pref(call: CallbackQuery, state: FSMContext):
    pref = call.data.split(":",1)[1]
    data = await state.get_data()
    user_id = call.from_user.id
    username = call.from_user.username or ""
    await save_profile(user_id, username, data['name'], data['gender'], data['about'], data['age'], data['city'], pref)
    await call.message.answer("Анкета сохранена!", reply_markup=main_menu())
    await state.clear()
    await call.answer()
