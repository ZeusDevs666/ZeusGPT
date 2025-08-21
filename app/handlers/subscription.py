# app/handlers/subscription.py
from __future__ import annotations
import contextlib
from aiogram import Router, F, types
from app.config import settings
from app.services.checker import SubscriptionChecker
from app.services.subscription import build_channels_kb

router = Router(name="subscription")
_checker = SubscriptionChecker()

@router.callback_query(F.data == "check_sub")
async def on_check_subscription(call: types.CallbackQuery):
    user_id = call.from_user.id
    required = getattr(settings, "required_channels", []) or []
    ok = await _checker.is_subscribed(user_id)

    if ok:
        # меняем текст и показываем главное меню
        if call.message:
            await call.message.edit_text("✅ Подписка подтверждена!")
            await call.message.answer("<b>👋 Привет! Это ZeusGPT.</b> \nЯ могу ответить на любой твой вопрос! К сожалению я не сохраняю историю нашей переписки, но это пока.. \n\n  Задавай вопрос 👇")
        with contextlib.suppress(Exception):
            await call.answer("Подписка подтверждена ✅", show_alert=False)
        return

    # всё ещё нет подписки — повторно показываем кнопки
    kb = build_channels_kb(required)
    if call.message:
        await call.message.edit_text(
            "🚫 Всё ещё нет подписки.\n\n"
            "Подпишитесь и нажмите «Проверить подписку».",
            reply_markup=kb
        )
    with contextlib.suppress(Exception):
        await call.answer("Подписка не найдена 😕", show_alert=False)