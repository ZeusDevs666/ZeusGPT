# app/services/checker.py
import logging
from aiogram import Bot
from app.config import settings
from aiogram.client.default import DefaultBotProperties

logger = logging.getLogger(__name__)


class SubscriptionChecker:
    def __init__(self):
        token = settings.TELEGRAM_CHECKER_TOKEN
        if not token:
            raise RuntimeError("TELEGRAM_CHECKER_TOKEN не задан в .env")

        self.bot = Bot(
            token=token,
            default=DefaultBotProperties(parse_mode="HTML"),
        )

    async def is_subscribed(self, user_id: int) -> bool:
        """Проверяем подписку хотя бы на один из каналов из settings.REQUIRED_CHANNELS"""
        channels = [ch.strip() for ch in settings.REQUIRED_CHANNELS.split(",") if ch.strip()]
        if not channels:
            logger.warning("REQUIRED_CHANNELS пуст — подписка не проверяется")
            return True

        for channel in channels:
            try:
                member = await self.bot.get_chat_member(channel, user_id)
                if member.status in ("member", "administrator", "creator"):
                    return True
            except Exception as e:
                logger.warning(f"Не удалось проверить подписку {user_id} в {channel}: {e}")

        return False

    async def close(self):
        await self.bot.session.close()