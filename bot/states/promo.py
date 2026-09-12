from aiogram.fsm.state import State, StatesGroup


class PromoStates(StatesGroup):
    waiting_for_code = State()
