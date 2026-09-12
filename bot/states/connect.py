from aiogram.fsm.state import State, StatesGroup


class ConnectStates(StatesGroup):
    waiting_for_pairing_code = State()
