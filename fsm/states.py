from aiogram.fsm.state import State, StatesGroup

class ProfileForm(StatesGroup):
    name = State()
    gender = State()
    about = State()
    age = State()
    city = State()
    preference = State()

class EditForm(StatesGroup):
    edit_name = State()
    edit_gender = State()
    edit_about = State()
    edit_age = State()
    edit_city = State()
    edit_preference = State()
