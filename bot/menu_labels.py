from localization.loader import t

_MENU_KEYS = [
    "menu.connect_userbot",
    "menu.store",
    "menu.my_modules",
    "menu.my_account",
    "menu.promo",
    "menu.referrals",
    "menu.settings",
    "menu.help",
]

# A user mid-FSM-flow (typing a search query, about to send a zip, about
# to send a pairing code) can always bail out by tapping a main menu
# button instead - without this, that tap would get swallowed and
# misinterpreted as the expected input (e.g. "👤 Мой аккаунт" treated as
# a search query). Handlers scoped to an FSM state should add
# `~F.text.in_(ALL_MENU_LABELS)` alongside the state filter.
ALL_MENU_LABELS = {t(key, lang) for key in _MENU_KEYS for lang in ("ru", "en")}
