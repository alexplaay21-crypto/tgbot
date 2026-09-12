from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from api.backend_client import backend_client
from bot.keyboards.creator import (
    access_type_keyboard,
    category_choice_keyboard,
    creator_panel_keyboard,
    moderation_menu_keyboard,
    plan_choice_keyboard,
    promo_type_keyboard,
)
from bot.menu_labels import ALL_MENU_LABELS
from bot.states.creator import (
    CreatorModerationStates,
    CreatorModuleStates,
    CreatorPromoStates,
    CreatorVerifyStates,
)
from config.settings import settings
from localization.loader import t

router = Router(name="creator")


def _lang(backend_user: dict | None) -> str:
    return (backend_user or {}).get("language") or "ru"


def _is_creator(telegram_user_id: int) -> bool:
    return telegram_user_id in settings.creator_ids


async def _reject(obj, telegram_user_id: int) -> bool:
    if _is_creator(telegram_user_id):
        return False

    if isinstance(obj, CallbackQuery):
        await obj.answer()

    return True


def _reason(exc: Exception) -> str:
    response = getattr(exc, "response", None)
    if response is not None:
        try:
            data = response.json()
            return str(data.get("detail", data))
        except Exception:
            pass
    return str(exc)


# =========================
# PANEL
# =========================

@router.message(Command("creator"))
async def open_creator_panel(message: Message, backend_user: dict | None):
    if await _reject(message, message.from_user.id):
        return

    lang = _lang(backend_user)

    await message.answer(
        t("creator.panel_title", lang),
        reply_markup=creator_panel_keyboard(lang),
    )


@router.callback_query(F.data == "creator:panel")
async def back_to_panel(callback: CallbackQuery, backend_user: dict | None):
    if await _reject(callback, callback.from_user.id):
        return

    lang = _lang(backend_user)

    await callback.answer()
    await callback.message.edit_text(
        t("creator.panel_title", lang),
        reply_markup=creator_panel_keyboard(lang),
    )


# =========================
# ADD MODULE
# =========================

@router.callback_query(F.data == "creator:add_module")
async def add_module_start(
    callback: CallbackQuery,
    backend_user: dict | None,
    state: FSMContext,
):
    if await _reject(callback, callback.from_user.id):
        return

    lang = _lang(backend_user)

    await state.set_state(CreatorModuleStates.module_id)
    await callback.answer()
    await callback.message.edit_text(
        t("creator.module_id_prompt", lang)
    )


@router.message(
    CreatorModuleStates.module_id,
    ~F.text.in_(ALL_MENU_LABELS),
)
async def add_module_id(
    message: Message,
    backend_user: dict | None,
    state: FSMContext,
):
    lang = _lang(backend_user)
    value = (message.text or "").strip()

    if not value or len(value) > 64:
        await message.answer(t("creator.module_id_prompt", lang))
        return

    await state.update_data(module_id=value)
    await state.set_state(CreatorModuleStates.name)

    await message.answer(t("creator.module_name_prompt", lang))


@router.message(
    CreatorModuleStates.name,
    ~F.text.in_(ALL_MENU_LABELS),
)
async def add_module_name(
    message: Message,
    backend_user: dict | None,
    state: FSMContext,
):
    lang = _lang(backend_user)

    await state.update_data(name=(message.text or "").strip())
    await state.set_state(CreatorModuleStates.description)

    await message.answer(t("creator.module_description_prompt", lang))


@router.message(
    CreatorModuleStates.description,
    ~F.text.in_(ALL_MENU_LABELS),
)
async def add_module_description(
    message: Message,
    backend_user: dict | None,
    state: FSMContext,
):
    lang = _lang(backend_user)

    await state.update_data(
        description=(message.text or "").strip()
    )
    await state.set_state(CreatorModuleStates.category)

    await message.answer(
        t("creator.module_category_prompt", lang),
        reply_markup=category_choice_keyboard(lang),
    )


@router.callback_query(F.data.startswith("creator:category:"))
async def add_module_category(
    callback: CallbackQuery,
    backend_user: dict | None,
    state: FSMContext,
):
    if await _reject(callback, callback.from_user.id):
        return

    lang = _lang(backend_user)
    category = callback.data.split(":", 2)[2]

    if category == "none":
        category = ""

    await state.update_data(category=category)
    await state.set_state(CreatorModuleStates.version)

    await callback.answer()
    await callback.message.edit_text(
        t("creator.module_version_prompt", lang)
    )


@router.message(
    CreatorModuleStates.version,
    ~F.text.in_(ALL_MENU_LABELS),
)
async def add_module_version(
    message: Message,
    backend_user: dict | None,
    state: FSMContext,
):
    lang = _lang(backend_user)

    await state.update_data(version=(message.text or "").strip())
    await state.set_state(CreatorModuleStates.access_type)

    await message.answer(
        t("creator.module_access_prompt", lang),
        reply_markup=access_type_keyboard(lang),
    )


@router.callback_query(F.data.startswith("creator:access:"))
async def add_module_access(
    callback: CallbackQuery,
    backend_user: dict | None,
    state: FSMContext,
):
    if await _reject(callback, callback.from_user.id):
        return

    lang = _lang(backend_user)
    access_type = callback.data.split(":", 2)[2]

    await state.update_data(access_type=access_type)
    await state.set_state(CreatorModuleStates.core_version)

    await callback.answer()
    await callback.message.edit_text(
        t("creator.module_core_version_prompt", lang)
    )


@router.message(
    CreatorModuleStates.core_version,
    ~F.text.in_(ALL_MENU_LABELS),
)
async def add_module_core_version(
    message: Message,
    backend_user: dict | None,
    state: FSMContext,
):
    lang = _lang(backend_user)
    value = (message.text or "").strip()

    if value == "/skip":
        value = ""

    await state.update_data(core_version=value)
    await state.set_state(CreatorModuleStates.icon)

    await message.answer(
        t("creator.module_icon_prompt", lang)
    )


@router.message(
    CreatorModuleStates.icon,
    ~F.text.in_(ALL_MENU_LABELS),
)
async def add_module_icon(
    message: Message,
    backend_user: dict | None,
    state: FSMContext,
):
    lang = _lang(backend_user)
    value = (message.text or "").strip()

    if value == "/skip":
        value = ""

    await state.update_data(icon=value)
    await state.set_state(CreatorModuleStates.zip)

    await message.answer(
        t("creator.module_zip_prompt", lang)
    )


@router.message(
    CreatorModuleStates.zip,
    F.document,
)
async def add_module_zip(
    message: Message,
    backend_user: dict | None,
    state: FSMContext,
):
    lang = _lang(backend_user)

    document = message.document

    if not document.file_name or not document.file_name.lower().endswith(".zip"):
        await message.answer(
            t("custom_module.send_zip_file", lang)
        )
        return

    if document.file_size and document.file_size > 10 * 1024 * 1024:
        await message.answer(
            t("custom_module.too_large", lang)
        )
        return

    try:
        file = await message.bot.get_file(document.file_id)

        from io import BytesIO

        buffer = BytesIO()
        await message.bot.download_file(file.file_path, buffer)
        data = buffer.getvalue()

        values = await state.get_data()

        result = await backend_client.upload_official_module(
            module_id=values["module_id"],
            name=values["name"],
            description=values.get("description", ""),
            category=values.get("category", ""),
            access_type=values["access_type"],
            core_version_requirement=values.get("core_version", ""),
            version=values["version"],
            icon_file_id=values.get("icon", ""),
            creator_telegram_id=message.from_user.id,
            filename=document.file_name,
            data=data,
        )

        await state.clear()

        await message.answer(
            t(
                "creator.module_uploaded",
                lang,
            )
            + f"\n\nID: {result.get('id', values['module_id'])}"
        )

    except Exception as exc:
        await state.clear()

        await message.answer(
            t(
                "creator.module_upload_failed",
                lang,
                reason=_reason(exc),
            )
        )


# =========================
# MANAGE MODULES
# =========================

@router.callback_query(F.data == "creator:manage_modules")
async def manage_modules(
    callback: CallbackQuery,
    backend_user: dict | None,
):
    if await _reject(callback, callback.from_user.id):
        return

    lang = _lang(backend_user)

    try:
        modules = await backend_client.list_modules()

        if not modules:
            text = t("creator.manage_modules_empty", lang)
        else:
            lines = [t("creator.manage_modules_title", lang), ""]

            for module in modules:
                lines.append(
                    f"• {module.get('name', module.get('id', '?'))}"
                    f" — `{module.get('id', '?')}`"
                    f"\n  v{module.get('current_version') or '?'}"
                    f" | {module.get('status', '?')}"
                    f" | verified={module.get('verified', False)}"
                )

            text = "\n".join(lines)

        await callback.answer()
        await callback.message.edit_text(text)

    except Exception as exc:
        await callback.answer()
        await callback.message.edit_text(
            t(
                "creator.manage_modules_error",
                lang,
                reason=_reason(exc),
            )
        )


# =========================
# VERIFY MODULE
# =========================

@router.callback_query(F.data == "creator:verify_module")
async def verify_module_start(
    callback: CallbackQuery,
    backend_user: dict | None,
    state: FSMContext,
):
    if await _reject(callback, callback.from_user.id):
        return

    lang = _lang(backend_user)

    await state.set_state(CreatorVerifyStates.module_id)
    await callback.answer()
    await callback.message.edit_text(
        t("creator.verify_module_prompt", lang)
    )


@router.message(
    CreatorVerifyStates.module_id,
    ~F.text.in_(ALL_MENU_LABELS),
)
async def verify_module_entered(
    message: Message,
    backend_user: dict | None,
    state: FSMContext,
):
    lang = _lang(backend_user)
    module_id = (message.text or "").strip()

    await state.clear()

    try:
        await backend_client.verify_module(
            module_id,
            message.from_user.id,
        )

        await message.answer(
            t(
                "creator.verify_module_success",
                lang,
                module_id=module_id,
            )
        )

    except Exception as exc:
        await message.answer(
            t(
                "creator.verify_module_failed",
                lang,
                reason=_reason(exc),
            )
        )


# =========================
# PROMO
# =========================

@router.callback_query(F.data == "creator:create_promo")
async def promo_start(
    callback: CallbackQuery,
    backend_user: dict | None,
    state: FSMContext,
):
    if await _reject(callback, callback.from_user.id):
        return

    lang = _lang(backend_user)

    await state.set_state(CreatorPromoStates.code)
    await callback.answer()
    await callback.message.edit_text(
        t("creator.promo_code_prompt", lang)
    )


@router.message(
    CreatorPromoStates.code,
    ~F.text.in_(ALL_MENU_LABELS),
)
async def promo_code(
    message: Message,
    backend_user: dict | None,
    state: FSMContext,
):
    lang = _lang(backend_user)

    await state.update_data(
        code=(message.text or "").strip().upper()
    )
    await state.set_state(CreatorPromoStates.type)

    await message.answer(
        t("creator.promo_type_prompt", lang),
        reply_markup=promo_type_keyboard(lang),
    )


@router.callback_query(F.data.startswith("creator:promotype:"))
async def promo_type(
    callback: CallbackQuery,
    backend_user: dict | None,
    state: FSMContext,
):
    if await _reject(callback, callback.from_user.id):
        return

    lang = _lang(backend_user)
    promo_type = callback.data.split(":", 2)[2]

    await state.update_data(type=promo_type)

    if promo_type == "plan_grant":
        await state.set_state(CreatorPromoStates.plan)
        text = t("creator.promo_plan_prompt", lang)
        markup = plan_choice_keyboard(lang)

    elif promo_type == "universal_days":
        await state.set_state(CreatorPromoStates.bonus_days)
        text = t("creator.promo_bonus_days_prompt", lang)
        markup = None

    else:
        await state.set_state(CreatorPromoStates.discount_percent)
        text = t("creator.promo_discount_prompt", lang)
        markup = None

    await callback.answer()
    await callback.message.edit_text(text, reply_markup=markup)


@router.callback_query(F.data.startswith("creator:promoplan:"))
async def promo_plan(
    callback: CallbackQuery,
    backend_user: dict | None,
    state: FSMContext,
):
    if await _reject(callback, callback.from_user.id):
        return

    lang = _lang(backend_user)
    plan = callback.data.split(":", 2)[2]

    await state.update_data(plan=plan)
    await state.set_state(CreatorPromoStates.bonus_days)

    await callback.answer()
    await callback.message.edit_text(
        t("creator.promo_bonus_days_prompt", lang)
    )


@router.message(
    CreatorPromoStates.discount_percent,
    ~F.text.in_(ALL_MENU_LABELS),
)
async def promo_discount(
    message: Message,
    backend_user: dict | None,
    state: FSMContext,
):
    lang = _lang(backend_user)

    try:
        value = int((message.text or "").strip())

        if not 1 <= value <= 100:
            raise ValueError

    except ValueError:
        await message.answer(
            t("creator.promo_invalid_discount", lang)
        )
        return

    await state.update_data(discount_percent=value)
    await state.set_state(CreatorPromoStates.usage_limit)

    await message.answer(
        t("creator.promo_usage_limit_prompt", lang)
    )


@router.message(
    CreatorPromoStates.bonus_days,
    ~F.text.in_(ALL_MENU_LABELS),
)
async def promo_bonus_days(
    message: Message,
    backend_user: dict | None,
    state: FSMContext,
):
    lang = _lang(backend_user)

    try:
        value = int((message.text or "").strip())

        if value < 1:
            raise ValueError

    except ValueError:
        await message.answer(
            t("creator.promo_invalid_number", lang)
        )
        return

    await state.update_data(bonus_days=value)
    await state.set_state(CreatorPromoStates.usage_limit)

    await message.answer(
        t("creator.promo_usage_limit_prompt", lang)
    )


@router.message(
    CreatorPromoStates.usage_limit,
    ~F.text.in_(ALL_MENU_LABELS),
)
async def promo_usage_limit(
    message: Message,
    backend_user: dict | None,
    state: FSMContext,
):
    lang = _lang(backend_user)
    value = (message.text or "").strip()

    if value == "/skip":
        limit = None
    else:
        try:
            limit = int(value)
            if limit < 1:
                raise ValueError
        except ValueError:
            await message.answer(
                t("creator.promo_invalid_number", lang)
            )
            return

    await state.update_data(usage_limit=limit)
    await state.set_state(CreatorPromoStates.expires_in_days)

    await message.answer(
        t("creator.promo_expires_prompt", lang)
    )


@router.message(
    CreatorPromoStates.expires_in_days,
    ~F.text.in_(ALL_MENU_LABELS),
)
async def promo_expires(
    message: Message,
    backend_user: dict | None,
    state: FSMContext,
):
    lang = _lang(backend_user)
    value = (message.text or "").strip()

    if value == "/skip":
        expires = None
    else:
        try:
            expires = int(value)
            if expires < 1:
                raise ValueError
        except ValueError:
            await message.answer(
                t("creator.promo_invalid_number", lang)
            )
            return

    data = await state.get_data()
    await state.clear()

    try:
        result = await backend_client.create_promo_code(
            code=data["code"],
            type_=data["type"],
            plan_code=data.get("plan"),
            bonus_days=data.get("bonus_days"),
            discount_percent=data.get("discount_percent"),
            usage_limit=data.get("usage_limit"),
            expires_in_days=expires,
            creator_telegram_id=message.from_user.id,
        )

        await message.answer(
            t(
                "creator.promo_created",
                lang,
                code=result.get("code", data["code"]),
            )
        )

    except Exception as exc:
        await message.answer(
            t(
                "creator.promo_create_failed",
                lang,
                reason=_reason(exc),
            )
        )


# =========================
# USERS
# =========================

@router.callback_query(F.data == "creator:users")
async def creator_users(
    callback: CallbackQuery,
    backend_user: dict | None,
):
    if await _reject(callback, callback.from_user.id):
        return

    lang = _lang(backend_user)

    try:
        users = await backend_client.list_admin_users(
            callback.from_user.id
        )

        if not users:
            text = t("creator.users_empty", lang)
        else:
            lines = [t("creator.users_title", lang), ""]

            for user in users:
                username = user.get("username") or "—"

                lines.append(
                    f"• {user.get('telegram_user_id')} "
                    f"@{username} "
                    f"| {user.get('status', 'unknown')}"
                )

            text = "\n".join(lines)

        await callback.answer()
        await callback.message.edit_text(text)

    except Exception as exc:
        await callback.answer()
        await callback.message.edit_text(
            t(
                "creator.users_error",
                lang,
                reason=_reason(exc),
            )
        )


# =========================
# STATS
# =========================

@router.callback_query(F.data == "creator:stats")
async def creator_stats(
    callback: CallbackQuery,
    backend_user: dict | None,
):
    if await _reject(callback, callback.from_user.id):
        return

    lang = _lang(backend_user)

    try:
        stats = await backend_client.get_admin_stats(
            callback.from_user.id
        )

        lines = [t("creator.stats_title", lang), ""]

        for key, value in stats.items():
            lines.append(f"• {key}: {value}")

        await callback.answer()
        await callback.message.edit_text(
            "\n".join(lines)
        )

    except Exception as exc:
        await callback.answer()
        await callback.message.edit_text(
            t(
                "creator.stats_error",
                lang,
                reason=_reason(exc),
            )
        )


# =========================
# MODERATION
# =========================

@router.callback_query(F.data == "creator:moderation")
async def open_moderation_menu(
    callback: CallbackQuery,
    backend_user: dict | None,
):
    if await _reject(callback, callback.from_user.id):
        return

    lang = _lang(backend_user)

    await callback.answer()
    await callback.message.edit_text(
        t("creator.moderation_title", lang),
        reply_markup=moderation_menu_keyboard(lang),
    )


@router.callback_query(F.data == "creator:modflag")
async def moderation_flag_start(
    callback: CallbackQuery,
    backend_user: dict | None,
    state: FSMContext,
):
    if await _reject(callback, callback.from_user.id):
        return

    lang = _lang(backend_user)

    await state.set_state(
        CreatorModerationStates.target_telegram_id
    )

    await callback.answer()
    await callback.message.edit_text(
        t("creator.ask_target_telegram_id", lang)
    )


@router.message(
    CreatorModerationStates.target_telegram_id,
    ~F.text.in_(ALL_MENU_LABELS),
)
async def moderation_flag_target(
    message: Message,
    backend_user: dict | None,
    state: FSMContext,
):
    lang = _lang(backend_user)
    text = (message.text or "").strip()

    if not text.isdigit():
        await message.answer(
            t("creator.invalid_number", lang)
        )
        return

    await state.update_data(
        target_telegram_id=int(text)
    )

    await state.set_state(
        CreatorModerationStates.reason
    )

    await message.answer(
        t("creator.ask_flag_reason", lang)
    )


@router.message(
    CreatorModerationStates.reason,
    ~F.text.in_(ALL_MENU_LABELS),
)
async def moderation_flag_reason(
    message: Message,
    backend_user: dict | None,
    state: FSMContext,
):
    lang = _lang(backend_user)
    reason = (message.text or "").strip()

    if not reason:
        await message.answer(
            t("creator.invalid_reason", lang)
        )
        return

    data = await state.get_data()
    await state.clear()

    try:
        await backend_client.flag_user(
            message.from_user.id,
            data["target_telegram_id"],
            reason,
        )

        await message.answer(
            t(
                "creator.moderation_flag_saved",
                lang,
                target=data["target_telegram_id"],
            )
        )

    except Exception as exc:
        await message.answer(
            t(
                "creator.moderation_flag_failed",
                lang,
                reason=_reason(exc),
            )
        )


@router.callback_query(F.data == "creator:modhistory")
async def moderation_history_start(
    callback: CallbackQuery,
    backend_user: dict | None,
    state: FSMContext,
):
    if await _reject(callback, callback.from_user.id):
        return

    lang = _lang(backend_user)

    await state.set_state(
        CreatorModerationStates.history_telegram_id
    )

    await callback.answer()
    await callback.message.edit_text(
        t("creator.ask_history_telegram_id", lang)
    )


@router.message(
    CreatorModerationStates.history_telegram_id,
    ~F.text.in_(ALL_MENU_LABELS),
)
async def moderation_history(
    message: Message,
    backend_user: dict | None,
    state: FSMContext,
):
    lang = _lang(backend_user)
    text = (message.text or "").strip()

    await state.clear()

    target_id = None

    if text != "/skip":
        if not text.isdigit():
            await message.answer(
                t("creator.invalid_number", lang)
            )
            return

        target_id = int(text)

    try:
        flags = await backend_client.list_moderation_flags(
            message.from_user.id,
            target_id,
        )

        if not flags:
            await message.answer(
                t("creator.no_flags", lang)
            )
            return

        lines = []

        for flag in flags:
            created = str(flag.get("created_at", ""))[:16]
            target = flag.get("target_id", "—")
            reason = flag.get("reason", "")

            lines.append(
                f"{created} — target {target} — {reason}"
            )

        await message.answer("\n".join(lines))

    except Exception as exc:
        await message.answer(
            t(
                "creator.moderation_flag_failed",
                lang,
                reason=_reason(exc),
            )
        )
