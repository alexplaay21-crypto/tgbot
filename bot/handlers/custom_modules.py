import httpx
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from api.backend_client import backend_client
from bot.keyboards.custom_module import custom_module_confirm_keyboard
from bot.menu_labels import ALL_MENU_LABELS
from bot.states.custom_module import CustomModuleStates
from localization.loader import t

router = Router(name="custom_modules")

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # matches Backend's custom_module_service limit


def _lang(backend_user: dict | None) -> str:
    return (backend_user or {}).get("language") or "ru"


async def _primary_account_id(telegram_user_id: int) -> int | None:
    accounts = await backend_client.list_accounts(telegram_user_id)
    primary = next((a for a in accounts if a["is_primary"]), None)
    return primary["id"] if primary else None


def _extract_reason(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        try:
            return exc.response.json().get("detail", str(exc))
        except Exception:
            return str(exc)
    return str(exc)


@router.callback_query(F.data == "mymod:custom_upload")
async def start_custom_upload(callback: CallbackQuery, backend_user: dict | None, state: FSMContext) -> None:
    lang = _lang(backend_user)
    await callback.answer()
    await state.set_state(CustomModuleStates.waiting_for_zip)
    await callback.message.edit_text(t("custom_module.upload_prompt", lang))


@router.message(CustomModuleStates.waiting_for_zip, ~F.text.in_(ALL_MENU_LABELS), F.document)
async def receive_custom_zip(message: Message, backend_user: dict | None, state: FSMContext) -> None:
    lang = _lang(backend_user)
    await state.clear()

    doc = message.document
    if not (doc.file_name or "").lower().endswith(".zip"):
        await message.answer(t("custom_module.not_a_zip", lang))
        return
    if doc.file_size and doc.file_size > MAX_UPLOAD_SIZE:
        await message.answer(t("custom_module.too_large", lang))
        return

    account_id = await _primary_account_id(message.from_user.id)
    if account_id is None:
        await message.answer(t("common.need_start", lang))
        return

    tg_file = await message.bot.get_file(doc.file_id)
    buffer = await message.bot.download_file(tg_file.file_path)
    data = buffer.read()

    fallback_name = (doc.file_name or "module").rsplit(".", 1)[0]
    try:
        module = await backend_client.upload_custom_module(account_id, fallback_name, doc.file_name or "module.zip", data)
    except Exception as exc:
        reason = _extract_reason(exc)
        if reason == "custom_vip_required":
            await message.answer(t("custom_module.vip_required", lang))
        else:
            await message.answer(t("custom_module.upload_failed", lang, reason=reason))
        return

    # Section 33: the mandatory risk warning, shown after technical
    # validation but before the user can actually confirm installation -
    # unless a Creator has already manually reviewed this exact upload
    # (module["verified"]), in which case a lighter confirmation is
    # enough. A brand-new upload is always unverified (see Backend's
    # custom_module_service - verification resets on every re-upload),
    # so this mostly matters for a module a Creator reviewed out of band
    # before the user tries to (re)install it.
    if module.get("verified"):
        text = t("custom_module.verified_notice", lang)
    else:
        text = t("custom_module.warning", lang)
    await message.answer(text, reply_markup=custom_module_confirm_keyboard(module["id"], lang))


@router.message(CustomModuleStates.waiting_for_zip, ~F.text.in_(ALL_MENU_LABELS))
async def receive_non_document(message: Message, backend_user: dict | None) -> None:
    await message.answer(t("custom_module.send_zip_file", _lang(backend_user)))


@router.callback_query(F.data.startswith("custommod:details:"))
async def custom_module_details(callback: CallbackQuery, backend_user: dict | None) -> None:
    await callback.answer(t("custom_module.details_text", _lang(backend_user)), show_alert=True)


@router.callback_query(F.data.startswith("custommod:cancel:"))
async def custom_module_cancel(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    await callback.answer()
    await callback.message.edit_text(t("custom_module.cancelled", lang))


@router.callback_query(F.data.startswith("custommod:install:"))
async def custom_module_install(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    module_id = callback.data.split(":", 2)[2]
    account_id = await _primary_account_id(callback.from_user.id)
    await callback.answer()
    if account_id is None:
        return

    try:
        await backend_client.install_module(account_id, module_id)
    except Exception as exc:
        await callback.message.edit_text(t("store.install_denied", lang, reason=_extract_reason(exc)))
        return

    await backend_client.create_command(account_id, "install_module", {"module_id": module_id})
    await callback.message.edit_text(t("store.install_sent", lang))
