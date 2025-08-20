from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models import User

router = Router(name="start")

async def upsert_user(session: AsyncSession, m: Message) -> User:
    is_premium = bool(getattr(m.from_user, "is_premium", False))
    u = await session.get(User, m.from_user.id)
    if u is None:
        u = User(
            id=m.from_user.id,
            username=m.from_user.username,
            first_name=m.from_user.first_name,
            last_name=m.from_user.last_name,
            lang=m.from_user.language_code,
            is_premium=is_premium,
        )
        session.add(u)
    else:
        u.username = m.from_user.username
        u.first_name = m.from_user.first_name
        u.last_name = m.from_user.last_name
        u.lang = m.from_user.language_code
        u.is_premium = is_premium
    await session.commit()
    return u

@router.message(CommandStart())
@router.message(Command("menu"))
async def on_start(message: Message, session: AsyncSession, users_api):
    if settings.MAINTENANCE_MODE:
        await message.answer(settings.MAINTENANCE_MESSAGE)
        return

    # сохраняем/обновляем юзера
    u = await upsert_user(session, message)
    # шлём на сервер (не роняем при ошибке)
    try:
        await users_api.upsert_user(
            tg_user_id=u.id,
            username=u.username,
            first_name=u.first_name,
            last_name=u.last_name,
            lang=u.lang,
            is_premium=u.is_premium,
        )
    except Exception:
        pass

    # показываем главное меню всегда
    await message.answer(
        "<b>👋 Привет! Это ZeusGPT.</b> \nЯ могу ответить на любой твой вопрос! К сожалению я не сохраняю историю нашей переписки, но это пока.. \n\nЗадавай вопрос 👇",
    )