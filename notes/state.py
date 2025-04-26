from aiogram.fsm.state import State, StatesGroup

class Authorizer(StatesGroup):
    auth = State()

class AppenderNotes(StatesGroup):
    description = State()
    created_at = State()

class Deleter(StatesGroup):
    index = State()