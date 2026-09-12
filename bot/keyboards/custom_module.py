from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from localization.loader import t


def custom_module_confirm_keyboard(module_id: str, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("custom_module.details_button", lang), callback_data=f"custommod:details:{module_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("custom_module.install_button", lang), callback_data=f"custommod:install:{module_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("custom_module.cancel_button", lang), callback_data=f"custommod:cancel:{module_id}"
                )
            ],
        ]
    )
