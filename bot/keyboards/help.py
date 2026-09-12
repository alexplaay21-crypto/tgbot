from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from localization.loader import t


def help_keyboard(lang: str, support_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t("help.support_button", lang), url=support_url)]]
    )
