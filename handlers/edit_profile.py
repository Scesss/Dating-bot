from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from keyboards.builders import get_edit_menu_kb, get_params_menu_kb
from states.profile_states import ProfileStates
from aiogram.filters import StateFilter

router = Router()

@router.message(StateFilter(ProfileStates.EDIT_PROFILE))
async def cmd_edit(message: types.Message, state: FSMContext):
    await message.answer(
        "Выберите действие:",
        reply_markup=get_edit_menu_kb()
    )

# Обработчики кнопок главного меню
@router.callback_query(F.data == "cancel_edit", StateFilter(ProfileStates.EDIT_PROFILE))
async def cancel_edit(callback: types.CallbackQuery):
    await callback.message.edit_text("Редактирование отменено")
    await callback.answer()

@router.callback_query(F.data == "refill_profile", StateFilter(ProfileStates.EDIT_PROFILE))
async def refill_profile(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Начните заполнение профиля заново")
    await callback.answer()

@router.callback_query(F.data == "edit_params", StateFilter(ProfileStates.EDIT_PROFILE))
async def edit_params(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Выберите параметр для редактирования:",
        reply_markup=get_params_menu_kb()
    )
    await callback.answer()

# Обработчики кнопок редактирования параметров
@router.callback_query(F.data == "back_to_edit_menu", StateFilter(ProfileStates.EDIT_PROFILE))
async def back_to_edit_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Выберите действие:",
        reply_markup=get_edit_menu_kb()
    )
    await callback.answer()

@router.callback_query(F.data == "edit_name", StateFilter(ProfileStates.EDIT_PROFILE))
async def edit_name(callback: types.CallbackQuery, state: FSMContext):
    
    await callback.answer()

@router.callback_query(F.data == "edit_age",  StateFilter(ProfileStates.EDIT_PROFILE))
async def edit_age(callback: types.CallbackQuery, state: FSMContext):
    
    await callback.answer()

@router.callback_query(F.data == "edit_bio", StateFilter(ProfileStates.EDIT_PROFILE))
async def edit_bio(callback: types.CallbackQuery, state: FSMContext):
    
    await callback.answer()

@router.callback_query(F.data == "edit_photo", StateFilter(ProfileStates.EDIT_PROFILE))
async def edit_photo(callback: types.CallbackQuery, state: FSMContext):
    
    await callback.answer()

@router.callback_query(F.data == "edit_geo", StateFilter(ProfileStates.EDIT_PROFILE))
async def edit_geo(callback: types.CallbackQuery, state: FSMContext):
    
    await callback.answer()