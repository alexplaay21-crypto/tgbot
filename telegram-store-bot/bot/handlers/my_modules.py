from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from api.backend_client import backend_client
from bot.keyboards.my_modules import my_module_detail_keyboard, my_modules_list_keyboard
from localization.loader import t

router = Router(name="my_modules")


def _lang(backend_user: dict | None) -> str:
    return (backend_user or {}).get("language") or "ru"


async def _primary_account_id(telegram_user_id: int) -> int | None:
    accounts = await backend_client.list_accounts(telegram_user_id)
    primary = next((a for a in accounts if a["is_primary"]), None)
    return primary["id"] if primary else None


async def _render_list(message: Message, telegram_user_id: int, lang: str, edit: bool) -> None:
    account_id = await _primary_account_id(telegram_user_id)
    if account_id is None:
        await message.answer(t("common.need_start", lang))
        return

    modules = await backend_client.list_installed_modules(account_id)
    text = t("my_modules.title", lang) if modules else t("my_modules.empty", lang)
    markup = my_modules_list_keyboard(modules, lang)

    if edit:
        await message.edit_text(text, reply_markup=markup)
    else:
        await message.answer(text, reply_markup=markup)


async def _render_detail(callback: CallbackQuery, lang: str, module_id: str) -> None:
    account_id = await _primary_account_id(callback.from_user.id)
    if account_id is None:
        return
    modules = await backend_client.list_installed_modules(account_id)
    module = next((m for m in modules if m["module_id"] == module_id), None)
    if module is None:
        await callback.message.edit_text(t("my_modules.empty", lang))
        return
    status = t("my_modules.status_enabled", lang) if module["enabled"] else t("my_modules.status_disabled", lang)
    text = t("my_modules.detail", lang, name=module["name"], version=module["version"], status=status)
    await callback.message.edit_text(text, reply_markup=my_module_detail_keyboard(module_id, module["enabled"], lang))


@router.message(F.text.in_({"📦 Мои модули", "📦 My Modules"}))
async def open_my_modules(message: Message, backend_user: dict | None) -> None:
    await _render_list(message, message.from_user.id, _lang(backend_user), edit=False)


@router.callback_query(F.data == "mymod:list")
async def back_to_list(callback: CallbackQuery, backend_user: dict | None) -> None:
    await callback.answer()
    await _render_list(callback.message, callback.from_user.id, _lang(backend_user), edit=True)


@router.callback_query(F.data.startswith("mymod:view:"))
async def view_installed_module(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    module_id = callback.data.split(":", 2)[2]
    await callback.answer()
    await _render_detail(callback, lang, module_id)


@router.callback_query(F.data.startswith("mymod:enable:"))
async def enable_module(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    module_id = callback.data.split(":", 2)[2]
    account_id = await _primary_account_id(callback.from_user.id)
    await callback.answer(t("my_modules.action_sent", lang))
    if account_id is None:
        return
    await backend_client.toggle_module(account_id, module_id, True)
    await backend_client.create_command(account_id, "enable_module", {"module_id": module_id})
    await _render_detail(callback, lang, module_id)


@router.callback_query(F.data.startswith("mymod:disable:"))
async def disable_module(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    module_id = callback.data.split(":", 2)[2]
    account_id = await _primary_account_id(callback.from_user.id)
    await callback.answer(t("my_modules.action_sent", lang))
    if account_id is None:
        return
    await backend_client.toggle_module(account_id, module_id, False)
    await backend_client.create_command(account_id, "disable_module", {"module_id": module_id})
    await _render_detail(callback, lang, module_id)


@router.callback_query(F.data.startswith("mymod:update:"))
async def update_module(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    module_id = callback.data.split(":", 2)[2]
    account_id = await _primary_account_id(callback.from_user.id)
    await callback.answer(t("my_modules.action_sent", lang))
    if account_id is None:
        return
    await backend_client.create_command(account_id, "update_module", {"module_id": module_id})


@router.callback_query(F.data.startswith("mymod:delete:"))
async def delete_module(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    module_id = callback.data.split(":", 2)[2]
    account_id = await _primary_account_id(callback.from_user.id)
    await callback.answer()
    if account_id is None:
        return
    await backend_client.uninstall_module(account_id, module_id)
    await backend_client.create_command(account_id, "uninstall_module", {"module_id": module_id})
    await callback.message.edit_text(t("my_modules.deleted", lang))


@router.callback_query(F.data.startswith("mymod:settings:"))
async def module_settings(callback: CallbackQuery, backend_user: dict | None) -> None:
    await callback.answer(t("common.coming_soon", _lang(backend_user)), show_alert=True)
