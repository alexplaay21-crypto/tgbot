from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from localization.loader import t


def settings_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("settings.language", lang), callback_data="settings:language")],
            [InlineKeyboardButton(text=t("settings.documents", lang), callback_data="settings:documents")],
        ]
    )
