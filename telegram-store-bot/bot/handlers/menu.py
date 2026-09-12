from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from api.backend_client import backend_client
from bot.handlers.account import open_account_view
from bot.keyboards.help import help_keyboard
from bot.keyboards.language import language_keyboard
from bot.keyboards.settings import settings_keyboard
from config.settings import settings
from localization.loader import t

router = Router(name="menu")


def _lang(backend_user: dict | None) -> str:
    return (backend_user or {}).get("language") or "ru"


_ACCOUNT_LABELS = {t("menu.my_account", "ru"), t("menu.my_account", "en")}
_SETTINGS_LABELS = {t("menu.settings", "ru"), t("menu.settings", "en")}
_HELP_LABELS = {t("menu.help", "ru"), t("menu.help", "en")}
_COMING_SOON_LABELS = {
    t("menu.referrals", "ru"),
    t("menu.referrals", "en"),
}


@router.message(F.text.in_(_ACCOUNT_LABELS))
async def menu_my_account(message: Message, backend_user: dict | None) -> None:
    if backend_user is None:
        await message.answer(t("common.need_start", "ru"))
        return
    await open_account_view(message, backend_user)


@router.message(F.text.in_(_SETTINGS_LABELS))
async def menu_settings(message: Message, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    await message.answer(t("settings.title", lang), reply_markup=settings_keyboard(lang))


@router.callback_query(F.data == "settings:language")
async def settings_language(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text(t("welcome.choose_language", "ru"), reply_markup=language_keyboard())


@router.callback_query(F.data == "settings:documents")
async def settings_documents(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    docs = await backend_client.current_documents()
    await callback.answer()

    lines = []
    for doc in docs:
        label = t(f"documents.type_{doc['document_type']}", lang)
        lines.append(f"{label}: {doc['url']}")
    await callback.message.edit_text("\n".join(lines) or t("common.coming_soon", lang))


@router.message(F.text.in_(_HELP_LABELS))
async def menu_help(message: Message, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    keyboard = help_keyboard(lang, settings.SUPPORT_URL) if settings.SUPPORT_URL else None
    await message.answer(t("help.title", lang), reply_markup=keyboard)


@router.message(F.text.in_(_COMING_SOON_LABELS))
async def menu_coming_soon(message: Message, backend_user: dict | None) -> None:
    await message.answer(t("common.coming_soon", _lang(backend_user)))
