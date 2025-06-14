from aiogram.fsm.state import State, StatesGroup

class ProfileStates(StatesGroup):
    NAME = State()
    AGE = State()
    GENDER = State()
    LOOKING_FOR = State()
    BIO = State()
    PHOTO = State()
    LOCATION = State()      # Make sure this exists
    CONFIRMATION = State()
    MENU = State()
    EDIT_PROFILE = State()