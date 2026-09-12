import httpx
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from api.backend_client import backend_client
from bot.keyboards.store import category_keyboard, module_card_keyboard, module_list_keyboard
from bot.menu_labels import ALL_MENU_LABELS
from bot.states.store import StoreStates
from localization.loader import t

router = Router(name="store")


def _lang(backend_user: dict | None) -> str:
    return (backend_user or {}).get("language") or "ru"


async def _primary_account_id(telegram_user_id: int) -> int | None:
    accounts = await backend_client.list_accounts(telegram_user_id)
    primary = next((a for a in accounts if a["is_primary"]), None)
    return primary["id"] if primary else None


def _access_label(module: dict, lang: str) -> str:
    return t("store.access_pro", lang) if module.get("access_type") == "pro" else t("store.access_free", lang)


def _extract_denial_reason(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        try:
            return exc.response.json().get("detail", str(exc))
        except Exception:
            return str(exc)
    return str(exc)


@router.message(F.text.in_({"🧩 Магазин модулей", "🧩 Module Store"}))
async def open_store(message: Message, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    await message.answer(t("store.title", lang), reply_markup=category_keyboard(lang))


@router.callback_query(F.data == "store:categories")
async def back_to_categories(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    await callback.answer()
    await callback.message.edit_text(t("store.title", lang), reply_markup=category_keyboard(lang))


@router.callback_query(F.data.startswith("store:category:"))
async def show_category(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    category = callback.data.split(":", 2)[2]
    modules = await backend_client.list_modules(category=category)
    await callback.answer()
    if not modules:
        await callback.message.edit_text(t("store.empty_category", lang), reply_markup=category_keyboard(lang))
        return
    await callback.message.edit_text(
        t(f"store.category_{category}", lang), reply_markup=module_list_keyboard(modules, lang)
    )


@router.callback_query(F.data == "store:search")
async def start_search(callback: CallbackQuery, backend_user: dict | None, state: FSMContext) -> None:
    lang = _lang(backend_user)
    await callback.answer()
    await state.set_state(StoreStates.waiting_for_search_query)
    await callback.message.edit_text(t("store.search_prompt", lang))


@router.message(StoreStates.waiting_for_search_query, ~F.text.in_(ALL_MENU_LABELS))
async def run_search(message: Message, backend_user: dict | None, state: FSMContext) -> None:
    lang = _lang(backend_user)
    await state.clear()
    query = (message.text or "").strip().lower()
    modules = await backend_client.list_modules()
    matches = [
        m for m in modules if query in m["name"].lower() or query in (m.get("description") or "").lower()
    ]
    if not matches:
        await message.answer(t("store.search_empty", lang), reply_markup=category_keyboard(lang))
        return
    await message.answer(t("store.title", lang), reply_markup=module_list_keyboard(matches, lang))


@router.callback_query(F.data.startswith("store:view:"))
async def view_module(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    module_id = callback.data.split(":", 2)[2]
    module = await backend_client.get_module(module_id)
    await callback.answer()
    text = t(
        "store.module_card",
        lang,
        name=module["name"],
        description=module.get("description") or "",
        version=module.get("current_version") or "?",
        access=_access_label(module, lang),
    )
    await callback.message.edit_text(text, reply_markup=module_card_keyboard(module_id, lang))


@router.callback_query(F.data.startswith("store:install:"))
async def install_module(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    module_id = callback.data.split(":", 2)[2]
    account_id = await _primary_account_id(callback.from_user.id)
    await callback.answer()
    if account_id is None:
        await callback.message.answer(t("common.need_start", lang))
        return

    try:
        await backend_client.install_module(account_id, module_id)
    except Exception as exc:
        await callback.message.answer(t("store.install_denied", lang, reason=_extract_denial_reason(exc)))
        return

    # Backend authorized it (section 28) - now tell Core to actually go
    # fetch and load it (section 51, Core polls for this).
    await backend_client.create_command(account_id, "install_module", {"module_id": module_id})
    await callback.message.answer(t("store.install_sent", lang))
