from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config.settings import settings
from localization.loader import t


def connect_warning_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("connect.proceed_button", lang), callback_data="connect:proceed")],
            [InlineKeyboardButton(text=t("connect.cancel_button", lang), callback_data="connect:cancel")],
        ]
    )


def server_choice_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Section 73's two-button choice: self-hosted vs platform-hosted."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("connect.own_server_button", lang), callback_data="connect:own_server")],
            [
                InlineKeyboardButton(
                    text=t("connect.platform_server_button", lang), callback_data="connect:platform_server"
                )
            ],
        ]
    )


def install_options_keyboard(lang: str) -> InlineKeyboardMarkup | None:
    """Self-hosting guides (Termux or VPS) - the user runs Core
    themselves, so the phone/OTP/2FA handshake happens directly in Core,
    never in this bot (sections 44-45)."""
    rows = []
    if settings.GITHUB_URL:
        rows.append([InlineKeyboardButton(text=t("connect.github_button", lang), url=settings.GITHUB_URL)])
    if settings.TERMUX_GUIDE_URL:
        rows.append([InlineKeyboardButton(text=t("connect.termux_button", lang), url=settings.TERMUX_GUIDE_URL)])
    if settings.VPS_GUIDE_URL:
        rows.append([InlineKeyboardButton(text=t("connect.vps_button", lang), url=settings.VPS_GUIDE_URL)])
    if settings.CORE_INSTALL_URL:
        rows.append(
            [InlineKeyboardButton(text=t("connect.install_guide_button", lang), url=settings.CORE_INSTALL_URL)]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None


def platform_server_keyboard(lang: str) -> InlineKeyboardMarkup | None:
    if not settings.SUPPORT_URL:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t("help.support_button", lang), url=settings.SUPPORT_URL)]]
    )
