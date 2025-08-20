# app/main.py
import asyncio
import logging
import contextlib
from .handlers.subscription import router as subscription_router
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .db import init_db, async_session
from .handlers import start, chat

# сервисы
from .services.llm import LLMClient
from .services.api_client import UsersAPI
from .services.checker import SubscriptionChecker
from .services.subscription import SubscriptionMiddleware  # мидлварь проверки подписки


# ---------------- logging ----------------
def setup_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


# ---------------- middlewares ----------------
class SessionMiddleware:
    """Пробрасываем AsyncSession в хэндлеры как `session`."""
    def __init__(self, factory: sessionmaker):
        self.factory = factory

    async def __call__(self, handler, event, data):
        async with self.factory() as session:
            data["session"] = session  # type: AsyncSession
            return await handler(event, data)


class LLMMiddleware:
    """Пробрасываем клиента LLM как `llm`."""
    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def __call__(self, handler, event, data):
        data["llm"] = self.llm
        return await handler(event, data)


class UsersAPIMiddleware:
    """Пробрасываем клиента серверных эндпоинтов (users) как `users_api`."""
    def __init__(self, api: UsersAPI):
        self.api = api

    async def __call__(self, handler, event, data):
        data["users_api"] = self.api
        return await handler(event, data)


# ---------------- main ----------------
async def main() -> None:
    setup_logging()
    await init_db()

    # основной бот (общается с пользователями)
    bot = Bot(
        token=settings.TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # роутеры
    dp.include_router(start.router)
    dp.include_router(chat.router)
    dp.include_router(subscription_router)
    # ресурсы
    llm = LLMClient()
    users_api = UsersAPI()
    checker = SubscriptionChecker()  # бот-наблюдатель для проверки подписки

    try:
        await llm.start()
        await users_api.start()
    except Exception:
        with contextlib.suppress(Exception):
            await llm.close()
        with contextlib.suppress(Exception):
            await users_api.close()
        raise

    # порядок мидлварей важен: сначала DI, затем блокирующие
    dp.message.middleware(SessionMiddleware(async_session))
    dp.callback_query.middleware(SessionMiddleware(async_session))

    dp.message.middleware(LLMMiddleware(llm))
    dp.callback_query.middleware(LLMMiddleware(llm))

    dp.message.middleware(UsersAPIMiddleware(users_api))
    dp.callback_query.middleware(UsersAPIMiddleware(users_api))

    # проверка подписки вторым ботом — на любое сообщение/коллбек
    dp.message.middleware(SubscriptionMiddleware(checker))
    dp.callback_query.middleware(SubscriptionMiddleware(checker))

    # снимаем вебхук (polling)
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    finally:
        await llm.close()
        await users_api.close()
        close = getattr(checker, "close", None)
        if callable(close):
            with contextlib.suppress(Exception):
                await close()


if __name__ == "__main__":
    asyncio.run(main())