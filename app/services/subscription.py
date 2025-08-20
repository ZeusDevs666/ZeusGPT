# app/services/subscription.py
from __future__ import annotations

import contextlib
from typing import List
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery

from app.config import settings
from app.services.checker import SubscriptionChecker


def build_channels_kb(channels: List[str]) -> InlineKeyboardMarkup:
    """
    Собираем клавиатуру:
      - на каждый канал: кнопка со ссылкой (работает для @username);
        для id (-100...) ссылку не можем сделать без инвайта, поэтому кнопку не добавляем.
      - в конце: кнопка 'Проверить подписку'
    """
    rows: List[List[InlineKeyboardButton]] = []
    for ch in channels:
        ch = ch.strip()
        if not ch:
            continue
        if ch.startswith("@"):
            url = f"https://t.me/{ch.lstrip('@')}"
            rows.append([InlineKeyboardButton(text=f"📢 Перейти в {ch}", url=url)])
        else:
            # id канала без публичного username — ссылку не строим
            rows.append([InlineKeyboardButton(text=f"📢 Канал {ch}", url="https://t.me")])  # заглушка
    rows.append([InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


class SubscriptionMiddleware:
    """
    Блокируем любые события от не подписанных пользователей.
    Если не подписан — отправляем сообщение с кнопками.
    """
    def __init__(self, checker: SubscriptionChecker):
        self.checker = checker

    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if user is None:
            return await handler(event, data)

        required = getattr(settings, "required_channels", []) or []
        if not required:
            # нет требований — пропускаем
            return await handler(event, data)

        is_ok = await self.checker.is_subscribed(user.id)  # <-- только user.id
        if not is_ok:
            kb = build_channels_kb(required)
            text = (
                "🚫 Доступ только для подписчиков.\n\n"
                "Подпишись на канал(ы), затем нажми «Проверить подписку» 👇"
            )
            # отсылаем ответ корректно для обоих типов событий
            if isinstance(event, Message):
                await event.answer(text, reply_markup=kb)
            elif isinstance(event, CallbackQuery):
                # короткий ответ на коллбек, чтобы убрать «часики»
                with contextlib.suppress(Exception):
                    await event.answer()
                if event.message:
                    await event.message.answer(text, reply_markup=kb)
            return  # прерываем цепочку — хэндлеры не вызовутся

        return await handler(event, data)