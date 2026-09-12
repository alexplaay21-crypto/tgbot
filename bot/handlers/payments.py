from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from api.backend_client import backend_client
from bot.keyboards.plans import duration_keyboard, plans_list_keyboard, vip_pay_keyboard
from localization.loader import t
from payments.pricing import CUSTOM_VIP_STARS

router = Router(name="payments")

_PLAN_NAMES = {"basic": {"ru": "Basic", "en": "Basic"}, "pro": {"ru": "Pro", "en": "Pro"}, "duo": {"ru": "Duo", "en": "Duo"}}


def _lang(backend_user: dict | None) -> str:
    return (backend_user or {}).get("language") or "ru"


@router.callback_query(F.data == "account:manage_sub")
async def show_plans(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    await callback.answer()
    await callback.message.answer(t("plans.choose_plan", lang), reply_markup=plans_list_keyboard(lang))


@router.callback_query(F.data.startswith("plan:select:"))
async def select_plan(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    code = callback.data.split(":", 2)[2]

    plans = await backend_client.list_plans()
    plan = next((p for p in plans if p["code"] == code), None)
    await callback.answer()
    if plan is None or not plan["prices"]:
        await callback.message.answer(t("common.generic_error", lang))
        return

    await callback.message.answer(t("plans.choose_duration", lang), reply_markup=duration_keyboard(code, plan["prices"], lang))


@router.callback_query(F.data.startswith("plan:pay:"))
async def pay_for_plan(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    _, _, code, duration = callback.data.split(":", 3)

    # Prices are re-fetched fresh right before the invoice goes out, so
    # there's no stale-price window between showing a button and paying.
    plans = await backend_client.list_plans()
    plan = next((p for p in plans if p["code"] == code), None)
    price_entry = next((p for p in (plan or {}).get("prices", []) if p["duration"] == duration), None)
    await callback.answer()
    if price_entry is None:
        await callback.message.answer(t("common.generic_error", lang))
        return

    plan_name = _PLAN_NAMES.get(code, {}).get(lang, code)
    await callback.message.answer_invoice(
        title=plan_name,
        description=t("plans.invoice_description", lang, plan=plan_name),
        payload=f"sub:{code}:{duration}",
        currency="XTR",
        prices=[LabeledPrice(label=plan_name, amount=price_entry["stars_amount"])],
        provider_token="",  # Telegram Stars need no payment provider
    )


@router.callback_query(F.data == "vip:info")
async def vip_info(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    await callback.answer()
    await callback.message.answer(
        t("plans.custom_vip_description", lang, stars=CUSTOM_VIP_STARS),
        reply_markup=vip_pay_keyboard(lang),
    )


@router.callback_query(F.data == "vip:pay")
async def pay_for_vip(callback: CallbackQuery, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    await callback.answer()
    title = t("plans.custom_vip_title", lang)
    await callback.message.answer_invoice(
        title=title,
        description=t("plans.custom_vip_description", lang, stars=CUSTOM_VIP_STARS),
        payload="custom_vip",
        currency="XTR",
        prices=[LabeledPrice(label=title, amount=CUSTOM_VIP_STARS)],
        provider_token="",
    )


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery) -> None:
    # Section 52: nothing extra to validate here - the price was pulled
    # fresh from Backend immediately before the invoice was sent.
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message, backend_user: dict | None) -> None:
    lang = _lang(backend_user)
    payment = message.successful_payment
    parts = payment.invoice_payload.split(":")

    if parts[0] == "sub":
        _, plan_code, duration = parts
        kind = "subscription"
    else:
        plan_code, duration, kind = None, None, "custom_vip"

    purchase = await backend_client.confirm_payment(
        telegram_user_id=message.from_user.id,
        kind=kind,
        plan_code=plan_code,
        duration=duration,
        stars_amount=payment.total_amount,
        provider_charge_id=payment.telegram_payment_charge_id,
    )
    await message.answer(t("plans.payment_success", lang, stars=purchase["stars_amount"]))
