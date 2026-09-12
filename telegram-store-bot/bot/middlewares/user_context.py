from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from api.backend_client import backend_client
from bot.menu_labels import ALL_MENU_LABELS


class UserContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        telegram_user_id = None
        if isinstance(event, Message) and event.from_user:
            telegram_user_id = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            telegram_user_id = event.from_user.id

        user = None
        if telegram_user_id is not None:
            user = await backend_client.get_user_by_telegram_id(telegram_user_id)
        data["backend_user"] = user

        # A main-menu tap always means "leave whatever flow I was in"
        # (search, zip upload, pairing code, ...) - clear any leftover
        # FSM state here, centrally, so individual flows only need to
        # exclude menu labels from their OWN handler (to let the tap fall
        # through to menu.py) without also having to remember to clear
        # state themselves.
        if isinstance(event, Message) and event.text in ALL_MENU_LABELS:
            fsm_context = data.get("state")
            if fsm_context is not None:
                await fsm_context.clear()

        return await handler(event, data)
