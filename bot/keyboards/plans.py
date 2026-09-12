from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from localization.loader import t

_DURATION_LABELS = {
    "month": {"ru": "1 месяц", "en": "1 month"},
    "three_months": {"ru": "3 месяца", "en": "3 months"},
    "year": {"ru": "1 год", "en": "1 year"},
}

_PLAN_TITLES = {
    "basic": {"ru": "⭐ Basic", "en": "⭐ Basic"},
    "pro": {"ru": "⭐ Pro", "en": "⭐ Pro"},
    "duo": {"ru": "⭐ Duo", "en": "⭐ Duo"},
}


def plans_list_keyboard(lang: str) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=_PLAN_TITLES[code][lang], callback_data=f"plan:select:{code}")]
        for code in ("basic", "pro", "duo")
    ]
    rows.append([InlineKeyboardButton(text=t("plans.custom_vip_title", lang), callback_data="vip:info")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def duration_keyboard(code: str, prices: list[dict], lang: str) -> InlineKeyboardMarkup:
    rows = []
    for price in prices:
        label = _DURATION_LABELS.get(price["duration"], {}).get(lang, price["duration"])
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{label} — {price['stars_amount']}⭐",
                    callback_data=f"plan:pay:{code}:{price['duration']}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def vip_pay_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t("plans.custom_vip_buy", lang), callback_data="vip:pay")]]
    )
