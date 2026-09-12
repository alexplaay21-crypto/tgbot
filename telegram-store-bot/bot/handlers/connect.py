import httpx
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from api.backend_client import backend_client
from bot.keyboards.connect import (
    connect_warning_keyboard,
    install_options_keyboard,
    platform_server_keyboard,
    server_choice_keyboard,
)
from bot.menu_labels import ALL_MENU_LABELS
from bot.states.connect import ConnectStates
from localization.loader import t

router = Router(name="connect")


def _lang(backend_user: dict | None) -> str:
    return (backend_user or {}).get("language") or "ru"


def _extract_reason(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        try:
            return exc.response.json().get("detail", str(exc))
        except Exception:
            return str(exc)
    return str(exc)


@router.message(F.text.in_({"🖥 Подключить Userbot", "🖥 Connect Userbot"}))
async def start_connect(message: Message, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    await message.answer(t("connect.warning", lang), reply_markup=connect_warning_keyboard(lang))


@router.callback_query(F.data == "connect:cancel")
async def cancel_connect(callback: CallbackQuery, backend_user: dict | None) -> None:
    await callback.answer()
    await callback.message.edit_text(t("connect.cancelled", _lang(backend_user)))


@router.callback_query(F.data == "connect:proceed")
async def show_server_choice(callback: CallbackQuery, backend_user: dict | None) -> None:
    """Section 73's fork: self-hosted (Termux/VPS) vs platform-hosted."""
    lang = _lang(backend_user)
    await callback.answer()
    await callback.message.edit_text(t("connect.choose_server", lang), reply_markup=server_choice_keyboard(lang))


@router.callback_query(F.data == "connect:own_server")
async def show_install_options(callback: CallbackQuery, backend_user: dict | None, state: FSMContext) -> None:
    lang = _lang(backend_user)
    await callback.answer()
    await state.set_state(ConnectStates.waiting_for_pairing_code)
    await callback.message.edit_text(
        t("connect.install_options", lang), reply_markup=install_options_keyboard(lang)
    )


@router.callback_query(F.data == "connect:platform_server")
async def platform_server_info(callback: CallbackQuery, backend_user: dict | None) -> None:
    """
    Deliberately does NOT ask for a phone number, login code, or 2FA
    password here, or anywhere in this bot. Collecting those through a
    shared bot process is functionally identical to a Telegram
    account-takeover scam regardless of intent, and sections 44-45/102
    are explicit that Backend/Bot must never see them - only Core,
    running locally, ever performs that handshake. A real "platform
    server" offering needs the same handshake to happen against an
    isolated Core process the user (or a support agent, with the
    customer present) logs into directly - not something this chat flow
    can safely automate, so for now this points to support instead.
    """
    lang = _lang(backend_user)
    await callback.answer()
    await callback.message.edit_text(
        t("connect.platform_server_info", lang), reply_markup=platform_server_keyboard(lang)
    )


@router.message(ConnectStates.waiting_for_pairing_code, ~F.text.in_(ALL_MENU_LABELS))
async def receive_pairing_code(message: Message, backend_user: dict | None, state: FSMContext) -> None:
    lang = _lang(backend_user)
    code = (message.text or "").strip().upper()
    if not code or len(code) > 16:
        await message.answer(t("connect.send_code_only", lang))
        return

    try:
        result = await backend_client.confirm_pairing(code, message.from_user.id)
    except Exception as exc:
        await message.answer(t("connect.confirm_failed", lang, reason=_extract_reason(exc)))
        return

    await state.clear()
    label = (
        t("connect.primary_connected", lang) if result["is_primary"] else t("connect.secondary_connected", lang)
    )
    await message.answer(f"{t('connect.success', lang)}\n\n{label}")
