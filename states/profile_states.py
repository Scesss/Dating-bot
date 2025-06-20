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
    BROWSING = State()
    EDIT_AGE = State()
    EDIT_GENDER = State()
    EDIT_BIO = State()
    EDIT_PHOTO = State()
    RESTART = State()
    LIKES = State()  # when cycling through who liked you
    MATCHES = State()  # when cycling through your mutual matches

