import httpx
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from api.backend_client import backend_client
from bot.menu_labels import ALL_MENU_LABELS
from bot.states.promo import PromoStates
from localization.loader import t

router = Router(name="promo")


def _lang(backend_user: dict | None) -> str:
    return (backend_user or {}).get("language") or "ru"


def _extract_reason(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        try:
            detail = exc.response.json().get("detail")
            if detail:
                return str(detail)
        except Exception:
            pass
    return str(exc)


@router.message(F.text.in_({"🎟 Промокод", "🎟 Promo Code"}))
async def start_promo(message: Message, backend_user: dict | None, state: FSMContext) -> None:
    lang = _lang(backend_user)

    await state.set_state(PromoStates.waiting_for_code)
    await message.answer(t("promo.promo_enter", lang))


@router.message(
    PromoStates.waiting_for_code,
    ~F.text.in_(ALL_MENU_LABELS),
)
async def receive_promo_code(
    message: Message,
    backend_user: dict | None,
    state: FSMContext,
) -> None:
    lang = _lang(backend_user)
    code = (message.text or "").strip()

    if not code:
        await message.answer(t("promo.promo_enter", lang))
        return

    try:
        result = await backend_client.redeem_promo_code(
            message.from_user.id,
            code,
        )
    except Exception as exc:
        await state.clear()
        await message.answer(
            t(
                "promo.promo_failed",
                lang,
                reason=_extract_reason(exc),
            )
        )
        return

    await state.clear()

    promo_type = result.get("type")
    days = result.get("bonus_days") or 0
    discount = result.get("discount_percent")
    plan = result.get("plan_code")

    if promo_type == "plan_grant":
        await message.answer(
            t(
                "promo.promo_success_plan",
                lang,
                plan=plan or "—",
                days=days,
            )
        )
    elif promo_type == "universal_days":
        await message.answer(
            t(
                "promo.promo_success_days",
                lang,
                days=days,
            )
        )
    elif promo_type == "discount":
        await message.answer(
            t(
                "promo.promo_success_discount",
                lang,
                discount=discount or 0,
            )
        )
    else:
        await message.answer(t("promo.promo_success", lang))
