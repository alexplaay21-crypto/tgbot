from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from localization.loader import t


def my_modules_list_keyboard(modules: list[dict], lang: str) -> InlineKeyboardMarkup:
    rows = []
    for m in modules:
        mark = "🟢" if m["enabled"] else "🔴"
        rows.append([InlineKeyboardButton(text=f"{mark} {m['name']}", callback_data=f"mymod:view:{m['module_id']}")])
    rows.append(
        [InlineKeyboardButton(text=t("custom_module.upload_button", lang), callback_data="mymod:custom_upload")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def my_module_detail_keyboard(module_id: str, enabled: bool, lang: str) -> InlineKeyboardMarkup:
    toggle_button = (
        InlineKeyboardButton(text=t("my_modules.disable_button", lang), callback_data=f"mymod:disable:{module_id}")
        if enabled
        else InlineKeyboardButton(text=t("my_modules.enable_button", lang), callback_data=f"mymod:enable:{module_id}")
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [toggle_button],
            [
                InlineKeyboardButton(
                    text=t("my_modules.update_button", lang), callback_data=f"mymod:update:{module_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("my_modules.delete_button", lang), callback_data=f"mymod:delete:{module_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("my_modules.settings_button", lang), callback_data=f"mymod:settings:{module_id}"
                )
            ],
            [InlineKeyboardButton(text=t("store.back_button", lang), callback_data="mymod:list")],
        ]
    )
