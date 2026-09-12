import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent

from api.backend_client import backend_client
from bot.handlers import account, connect, creator, custom_modules, menu, my_modules, payments, promo, start, store
from bot.middlewares.user_context import UserContextMiddleware
from config.settings import settings

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger("bot")


async def main() -> None:
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())  # explicit: store.py's search prompt needs FSM state

    dp.message.middleware(UserContextMiddleware())
    dp.callback_query.middleware(UserContextMiddleware())

    dp.include_router(start.router)
    dp.include_router(account.router)
    dp.include_router(payments.router)
    dp.include_router(store.router)
    dp.include_router(my_modules.router)
    dp.include_router(custom_modules.router)
    dp.include_router(connect.router)
    dp.include_router(creator.router)
    dp.include_router(promo.router)
    dp.include_router(menu.router)

    @dp.error()
    async def on_error(event: ErrorEvent) -> bool:
        # Section 70: the user only ever sees a short, friendly message -
        # full details go to the logs only.
        logger.exception("Update failed", exc_info=event.exception)
        update = event.update
        try:
            if update.message:
                await update.message.answer("❌ Что-то пошло не так. Попробуйте позже. / Something went wrong.")
            elif update.callback_query:
                await update.callback_query.answer("❌ Error", show_alert=True)
        except Exception:
            pass
        return True

    try:
        await dp.start_polling(bot)
    finally:
        await backend_client.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
