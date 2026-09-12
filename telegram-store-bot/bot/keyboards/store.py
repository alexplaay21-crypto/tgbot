from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from localization.loader import t

# Creator-published modules need to use one of these exact category
# codes for their category to show up here - not specified further in
# the master prompt, documented in the README as a convention.
CATEGORIES = ["popular", "new", "utilities", "automation", "moderation"]


def category_keyboard(lang: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t(f"store.category_{code}", lang), callback_data=f"store:category:{code}")]
        for code in CATEGORIES
    ]
    rows.append([InlineKeyboardButton(text=t("store.search_button", lang), callback_data="store:search")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def module_list_keyboard(modules: list[dict], lang: str) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text=m["name"], callback_data=f"store:view:{m['id']}")] for m in modules]
    rows.append([InlineKeyboardButton(text=t("store.back_button", lang), callback_data="store:categories")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def module_card_keyboard(module_id: str, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("store.install_button", lang), callback_data=f"store:install:{module_id}")],
            [InlineKeyboardButton(text=t("store.back_button", lang), callback_data="store:categories")],
        ]
    )
