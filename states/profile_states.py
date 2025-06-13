from aiogram.dispatcher.filters.state import State, StatesGroup

class ProfileStates(StatesGroup):
    NAME = State()
    AGE = State()
    GENDER = State()
    LOOKING_FOR = State()
    BIO = State()
    PHOTO = State()
    CONFIRMATION = State()

