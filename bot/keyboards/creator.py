from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.store import CATEGORIES
from localization.loader import t


def creator_panel_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("creator.add_module", lang), callback_data="creator:add_module")],
            [InlineKeyboardButton(text=t("creator.manage_modules", lang), callback_data="creator:manage_modules")],
            [InlineKeyboardButton(text=t("creator.verify_module", lang), callback_data="creator:verify_module")],
            [InlineKeyboardButton(text=t("creator.create_promo", lang), callback_data="creator:create_promo")],
            [InlineKeyboardButton(text=t("creator.users", lang), callback_data="creator:users")],
            [InlineKeyboardButton(text=t("creator.stats", lang), callback_data="creator:stats")],
            [InlineKeyboardButton(text=t("creator.moderation", lang), callback_data="creator:moderation")],
        ]
    )


def moderation_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("creator.moderation_flag_button", lang), callback_data="creator:modflag")],
            [InlineKeyboardButton(text=t("creator.moderation_history_button", lang), callback_data="creator:modhistory")],
            [InlineKeyboardButton(text=t("creator.back_to_panel", lang), callback_data="creator:panel")],
        ]
    )


def category_choice_keyboard(lang: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t(f"store.category_{code}", lang), callback_data=f"creator:category:{code}")]
        for code in CATEGORIES
    ]
    rows.append([
        InlineKeyboardButton(
            text=t("creator.no_category", lang),
            callback_data="creator:category:none",
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def access_type_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("store.access_free", lang), callback_data="creator:access:free")],
            [InlineKeyboardButton(text=t("store.access_pro", lang), callback_data="creator:access:pro")],
        ]
    )


def promo_type_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("creator.promo_type_plan_grant", lang),
                    callback_data="creator:promotype:plan_grant",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("creator.promo_type_universal_days", lang),
                    callback_data="creator:promotype:universal_days",
                )
            ],
            [
                InlineKeyboardButton(
                    text=t("creator.promo_type_discount", lang),
                    callback_data="creator:promotype:discount",
                )
            ],
        ]
    )


def plan_choice_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Basic", callback_data="creator:promoplan:basic")],
            [InlineKeyboardButton(text="Pro", callback_data="creator:promoplan:pro")],
            [InlineKeyboardButton(text="Duo", callback_data="creator:promoplan:duo")],
        ]
    )
