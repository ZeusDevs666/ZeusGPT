# app/handlers/chat.py
from aiogram import Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..services.llm import LLMClient
from ..services.media import detect_media_kind, pick_best_photo, download_file

router = Router(name="chat")


def split_text(text: str, limit: int = 3900):
    pos = 0
    n = len(text)
    while pos < n:
        chunk = text[pos: pos + limit]
        yield chunk
        pos += len(chunk)


@router.message()
async def on_message(message: Message, session: AsyncSession, llm: LLMClient, users_api):
    # режим техработ
    if settings.MAINTENANCE_MODE:
        await message.answer(
            settings.MAINTENANCE_MESSAGE,
            disable_web_page_preview=True,
        )
        return

    # подписку уже проверяет SubscriptionMiddleware

    # пингуем сервер (last_seen) + актуализируем premium
    is_premium = bool(getattr(message.from_user, "is_premium", False))
    try:
        await users_api.seen(tg_user_id=message.from_user.id, is_premium=is_premium)
    except Exception:
        pass

    text = (message.text or "").strip()

    # базовая обработка медиа для MVP (пока только примечание)
    media_note = ""
    kind = detect_media_kind(message)
    if kind == "photo":
        best = pick_best_photo(message.photo)
        if best:
            try:
                _, meta = await download_file(message.bot, best.file_id)
                media_note = (
                    f"\n\n[Пользователь прислал фото: "
                    f"{meta.get('file_path')}, {meta.get('file_size')} bytes]"
                )
            except Exception:
                media_note = "\n\n[Пользователь прислал фото: загрузить не удалось]"
    elif kind and hasattr(message, kind):
        obj = getattr(message, kind)
        fid = obj.file_id
        try:
            _, meta = await download_file(message.bot, fid)
            media_note = (
                f"\n\n[Пользователь прислал {kind}: "
                f"{meta.get('file_path')}, {meta.get('file_size')} bytes]"
            )
        except Exception:
            media_note = f"\n\n[Пользователь прислал {kind}: загрузить не удалось]"

    if not text and not kind:
        await message.answer(
            "✍️ Напишите текст или пришлите медиа.",
            disable_web_page_preview=True,
        )
        return

    typing = await message.answer("⏳ Печатаю…", disable_web_page_preview=True)
    try:
        prompt = text or "(без текста)"
        prompt += media_note
        reply = await llm.ask_text(message.from_user.id, prompt)
    except Exception as e:
        try:
            await typing.delete()
        except Exception:
            pass
        await message.answer(
            f"⚠️ Я получил ошибку от API"
            f"\nЕсли ошибка повторяется — напишите об этом в чат {settings.SUPPORT_CHAT_URL}",
            disable_web_page_preview=True,
        )
        return

    try:
        await typing.delete()
    except Exception:
        pass

    for chunk in split_text(reply):
        await message.answer(
            chunk,
            disable_web_page_preview=True,
        )