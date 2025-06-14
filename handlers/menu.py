from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from handlers.common import cmd_start
from handlers.common import cmd_profile
from states.profile_states import ProfileStates
from keyboards.builders import *
from aiogram.filters import StateFilter
from services.geocoding import get_city_name
from utils.navigation import Navigation
from aiogram.filters import Command

router = Router()

@router.message(StateFilter(ProfileStates.MENU))
async def process_choose(message: types.Message, state: FSMContext):
    valid_answer = ["Смотреть Анкеты", "Моя Анкета", "Топ", "Сон"]
    if message.text not in valid_answer:
        return await message.answer("Нет такого варианта ответа")
    
    if message.text == "Моя Анкета":
        await cmd_profile(message, state)
        return
    elif message.text == "Смотреть Анкеты":
        return await message.answer("Пока такой функции нет")
    elif message.text == "Сон":
        return await message.answer("Пока такой функции нет")
    elif message.text == "Топ":
        return await message.answer("Пока такой функции нет")