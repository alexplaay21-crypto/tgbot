from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from api.backend_client import backend_client
from bot.keyboards.documents import document_keyboard
from bot.keyboards.language import language_keyboard
from bot.keyboards.main_menu import main_menu_keyboard
from localization.loader import t

router = Router(name="start")


async def _send_document_or_menu(message: Message, telegram_user_id: int, lang: str) -> None:
    pending = await backend_client.pending_documents(telegram_user_id)
    if pending:
        doc = pending[0]
        label = t(f"documents.type_{doc['document_type']}", lang)
        await message.answer(f"{label}\n\n{t('documents.intro', lang)}", reply_markup=document_keyboard(doc, lang))
    else:
        await message.answer(t("welcome.menu_ready", lang), reply_markup=main_menu_keyboard(lang))


async def _edit_to_document_or_menu(callback: CallbackQuery, telegram_user_id: int, lang: str) -> None:
    pending = await backend_client.pending_documents(telegram_user_id)
    if pending:
        doc = pending[0]
        label = t(f"documents.type_{doc['document_type']}", lang)
        await callback.message.edit_text(
            f"{label}\n\n{t('documents.intro', lang)}", reply_markup=document_keyboard(doc, lang)
        )
    else:
        # editMessageText can't attach a persistent ReplyKeyboardMarkup,
        # so the main menu has to go out as a fresh message.
        await callback.message.edit_text(t("documents.all_accepted", lang))
        await callback.message.answer(t("welcome.menu_ready", lang), reply_markup=main_menu_keyboard(lang))


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = await backend_client.auth_bot(message.from_user.id, message.from_user.username)
    lang = user.get("language")

    if not lang:
        await message.answer(t("welcome.choose_language", "ru"), reply_markup=language_keyboard())
        return

    await _send_document_or_menu(message, message.from_user.id, lang)


@router.callback_query(F.data.startswith("lang:"))
async def on_language_chosen(callback: CallbackQuery) -> None:
    lang = callback.data.split(":", 1)[1]
    telegram_user_id = callback.from_user.id
    await backend_client.set_language(telegram_user_id, lang)
    await callback.answer(t("welcome.language_set", lang))
    await _edit_to_document_or_menu(callback, telegram_user_id, lang)


@router.callback_query(F.data.startswith("accept_doc:"))
async def on_document_accepted(callback: CallbackQuery) -> None:
    _, document_type, version = callback.data.split(":", 2)
    telegram_user_id = callback.from_user.id

    user = await backend_client.get_user_by_telegram_id(telegram_user_id)
    lang = (user or {}).get("language") or "ru"

    await backend_client.accept_document(telegram_user_id, document_type, version)
    await callback.answer(t("documents.accepted", lang))
    await _edit_to_document_or_menu(callback, telegram_user_id, lang)
