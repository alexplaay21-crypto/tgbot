from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from localization.loader import t


def account_keyboard(account_id: int, is_duo: bool, lang: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t("account.manage_subscription", lang), callback_data="account:manage_sub")],
        [InlineKeyboardButton(text=t("account.my_devices", lang), callback_data=f"account:devices:{account_id}")],
        [InlineKeyboardButton(text=t("account.purchase_history", lang), callback_data="account:purchases")],
    ]
    if is_duo:
        rows.append([InlineKeyboardButton(text=t("account.switch_account", lang), callback_data="account:switch")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def account_switch_keyboard(accounts: list[dict], lang: str) -> InlineKeyboardMarkup:
    rows = []
    for acc in accounts:
        label = t("account.primary_label", lang) if acc["is_primary"] else t("account.secondary_label", lang)
        rows.append([InlineKeyboardButton(text=label, callback_data=f"account:view:{acc['id']}")])

    secondary = next((a for a in accounts if not a["is_primary"]), None)
    if secondary is not None:
        rows.append(
            [
                InlineKeyboardButton(
                    text=t("account.remove_secondary", lang), callback_data=f"account:remove:{secondary['id']}"
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def account_remove_confirm_keyboard(account_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("account.remove_yes", lang), callback_data=f"account:remove_confirmed:{account_id}"
                )
            ],
            [InlineKeyboardButton(text=t("account.remove_no", lang), callback_data="account:switch")],
        ]
    )
