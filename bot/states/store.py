from aiogram.fsm.state import State, StatesGroup


class StoreStates(StatesGroup):
    waiting_for_search_query = State()
