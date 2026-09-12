import httpx
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from api.backend_client import backend_client
from bot.keyboards.account import account_keyboard, account_remove_confirm_keyboard, account_switch_keyboard
from localization.loader import t

router = Router(name="account")

_PLAN_LABELS = {
    "free": {"ru": "🆓 Free", "en": "🆓 Free"},
    "basic": {"ru": "⭐ Basic", "en": "⭐ Basic"},
    "pro": {"ru": "⭐ Pro", "en": "⭐ Pro"},
    "duo": {"ru": "⭐ Duo", "en": "⭐ Duo"},
}


def _lang(backend_user: dict | None) -> str:
    return (backend_user or {}).get("language") or "ru"


def _extract_reason(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        try:
            return exc.response.json().get("detail", str(exc))
        except Exception:
            return str(exc)
    return str(exc)


async def open_account_view(message: Message, backend_user: dict) -> None:
    """
    Entry point from the main menu. Non-Duo customers (the common case)
    go straight to their one account, unchanged from before Stage 8.
    Duo customers see a switcher first (section 39 allows either
    "show the selected account" or "show both separately" - a switcher
    covers the former without cramming both onto one screen).
    """
    lang = _lang(backend_user)
    accounts = await backend_client.list_accounts(backend_user["telegram_user_id"])
    if not accounts:
        await message.answer(t("common.need_start", lang))
        return
    if len(accounts) == 1:
        await _render_account(message, backend_user, accounts[0], accounts, edit=False)
    else:
        await message.answer(t("account.choose_account", lang), reply_markup=account_switch_keyboard(accounts, lang))


async def _render_account(
    message: Message, backend_user: dict, account: dict, all_accounts: list[dict], edit: bool
) -> None:
    lang = _lang(backend_user)
    telegram_user_id = backend_user["telegram_user_id"]

    sub = await backend_client.get_subscription(telegram_user_id)
    plans = await backend_client.list_plans()
    plan_row = next((p for p in plans if p["code"] == sub["plan_code"]), None)
    module_limit = plan_row["module_limit_per_account"] if plan_row else "?"
    installed = await backend_client.list_installed_modules(account["id"])

    plan_label = _PLAN_LABELS.get(sub["plan_code"], {}).get(lang, sub["plan_code"])
    status_key = "account.status_active" if sub["status"] == "active" else "account.status_inactive"
    until_line = (
        t("account.until", lang, date=sub["expires_at"][:10])
        if sub.get("expires_at")
        else t("account.no_expiry", lang)
    )
    username = backend_user.get("username") or t("account.no_username", lang)

    is_duo = len(all_accounts) > 1
    title = t("account.title", lang)
    if is_duo:
        account_label = t("account.primary_label", lang) if account["is_primary"] else t("account.secondary_label", lang)
        title = f"{title} — {account_label}"

    text = "\n\n".join(
        [
            title,
            t("account.telegram", lang, username=username),
            f"{t('account.subscription', lang, plan=plan_label)}\n{t(status_key, lang)}\n{until_line}",
            t("account.modules_count", lang, count=len(installed), limit=module_limit),
            t("account.prefix_line", lang, prefix=account["prefix"]),
        ]
    )
    markup = account_keyboard(account["id"], is_duo, lang)

    if edit:
        await message.edit_text(text, reply_markup=markup)
    else:
        await message.answer(text, reply_markup=markup)


@router.callback_query(F.data == "account:switch")
async def show_switcher(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    await callback.answer()
    accounts = await backend_client.list_accounts(callback.from_user.id)
    await callback.message.edit_text(t("account.choose_account", lang), reply_markup=account_switch_keyboard(accounts, lang))


@router.callback_query(F.data.startswith("account:view:"))
async def switch_to_account(callback: CallbackQuery, backend_user: dict | None) -> None:
    account_id = int(callback.data.split(":", 2)[2])
    await callback.answer()
    accounts = await backend_client.list_accounts(callback.from_user.id)
    account = next((a for a in accounts if a["id"] == account_id), None)
    if account is None or backend_user is None:
        return
    await _render_account(callback.message, backend_user, account, accounts, edit=True)


@router.callback_query(F.data.startswith("account:devices:"))
async def account_devices(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    account_id = int(callback.data.split(":", 2)[2])
    await callback.answer()
    all_devices = await backend_client.get_devices(callback.from_user.id)
    devices = [d for d in all_devices if d["account_id"] == account_id]
    if not devices:
        await callback.message.answer(t("account.devices_empty", lang))
        return
    lines = [
        t("account.device_line", lang, name=d.get("device_name") or "—", status=d["status"]) for d in devices
    ]
    await callback.message.answer("\n".join(lines))


@router.callback_query(F.data.startswith("account:purchases"))
async def account_purchases(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    purchases = await backend_client.get_purchases(callback.from_user.id)
    await callback.answer()
    if not purchases:
        await callback.message.answer(t("account.purchases_empty", lang))
        return
    lines = [
        f"{p['kind']} — {p['stars_amount']}⭐ — {p['created_at'][:10]} — {p['status']}" for p in purchases
    ]
    await callback.message.answer("\n".join(lines))


@router.callback_query(F.data.startswith("account:remove:"))
async def confirm_remove_account(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    account_id = int(callback.data.split(":", 2)[2])
    await callback.answer()
    await callback.message.edit_text(
        t("account.remove_confirm", lang), reply_markup=account_remove_confirm_keyboard(account_id, lang)
    )


@router.callback_query(F.data.startswith("account:remove_confirmed:"))
async def remove_account(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    account_id = int(callback.data.split(":", 2)[2])
    await callback.answer()
    try:
        await backend_client.delete_account(account_id, callback.from_user.id)
    except Exception as exc:
        await callback.message.edit_text(t("account.remove_failed", lang, reason=_extract_reason(exc)))
        return
    await callback.message.edit_text(t("account.removed", lang))
