from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..config import settings
from ..models import User

router = Router(name="start")


async def upsert_local_user(session: AsyncSession, m: Message) -> User:
    """Сохраняем/обновляем юзера в локальной БД бота"""
    is_premium = bool(getattr(m.from_user, "is_premium", False))

    # ищем по tg_user_id, а не по id
    u = await session.scalar(
        select(User).where(User.tg_user_id == m.from_user.id)
    )

    if u is None:
        u = User(
            tg_user_id=m.from_user.id,
            username=m.from_user.username,
            first_name=m.from_user.first_name,
            last_name=m.from_user.last_name,
            language_code=m.from_user.language_code,
            is_premium=is_premium,
        )
        session.add(u)
    else:
        u.username = m.from_user.username
        u.first_name = m.from_user.first_name
        u.last_name = m.from_user.last_name
        u.language_code = m.from_user.language_code
        u.is_premium = is_premium

    await session.commit()
    return u


@router.message(CommandStart())
@router.message(Command("menu"))
async def on_start(message: Message, session: AsyncSession, users_api):
    if settings.MAINTENANCE_MODE:
        await message.answer(settings.MAINTENANCE_MESSAGE)
        return

    # сохраняем/обновляем локально
    u = await upsert_local_user(session, message)

    # шлём данные на сервер
    try:
        await users_api.upsert_user(
            tg_user_id=message.from_user.id,
            bot_token=settings.BOT_TOKEN,  # ⚡ обязательное поле
            username=u.username,
            first_name=u.first_name,
            last_name=u.last_name,
            language_code=u.language_code,
            is_premium=u.is_premium,
        )
    except Exception as e:
        # логируем, но не роняем бота
        print(f"[users_api.upsert_user] Ошибка: {e}")

    # показываем главное меню всегда
    await message.answer(
        "<b>👋 Привет! Это ZeusGPT.</b>\n"
        "Я могу ответить на любой твой вопрос! "
        "К сожалению, я пока не сохраняю историю переписки, но это временно.\n\n"
        "Задавай вопрос 👇",
    )