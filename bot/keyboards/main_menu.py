from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from localization.loader import t


def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("menu.connect_userbot", lang))],
            [KeyboardButton(text=t("menu.store", lang))],
            [KeyboardButton(text=t("menu.my_modules", lang)), KeyboardButton(text=t("menu.my_account", lang))],
            [KeyboardButton(text=t("menu.referrals", lang)), KeyboardButton(text=t("menu.settings", lang))],
            [KeyboardButton(text=t("menu.help", lang))],
        ],
        resize_keyboard=True,
    )
