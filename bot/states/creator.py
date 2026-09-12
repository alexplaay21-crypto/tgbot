from aiogram.fsm.state import State, StatesGroup


class CreatorModuleStates(StatesGroup):
    module_id = State()
    name = State()
    description = State()
    category = State()
    version = State()
    access_type = State()
    core_version = State()
    icon = State()
    zip = State()


class CreatorPromoStates(StatesGroup):
    code = State()
    type = State()
    plan = State()
    discount_percent = State()
    bonus_days = State()
    usage_limit = State()
    expires_in_days = State()


class CreatorVerifyStates(StatesGroup):
    module_id = State()


class CreatorModerationStates(StatesGroup):
    target_telegram_id = State()
    reason = State()
    history_telegram_id = State()
