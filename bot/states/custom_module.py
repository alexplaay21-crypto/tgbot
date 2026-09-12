from aiogram.fsm.state import State, StatesGroup


class CustomModuleStates(StatesGroup):
    waiting_for_zip = State()
