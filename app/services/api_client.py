# app/services/api_client.py
from __future__ import annotations

import aiohttp
from typing import Optional
from ..config import settings


class UsersAPI:
    """Клиент к эндпоинтам users на твоём сервере."""
    def __init__(self) -> None:
        self._http: Optional[aiohttp.ClientSession] = None

    async def start(self) -> None:
        if self._http is None:
            timeout = aiohttp.ClientTimeout(total=10)
            self._http = aiohttp.ClientSession(timeout=timeout)

    async def close(self) -> None:
        if self._http is not None:
            await self._http.close()
            self._http = None

    async def upsert_user(
        self,
        tg_user_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        lang: str | None,
        is_premium: bool,
    ) -> None:
        """Создать/обновить пользователя на сервере. Ошибки не роняют бота."""
        if self._http is None:
            return
        payload = {
            "tg_user_id": tg_user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "lang": lang,
            "is_premium": is_premium,
        }
        try:
            async with self._http.post(settings.USERS_UPSERT_URL, json=payload) as resp:
                _ = await resp.text()  # читаем, но игнорим статус
        except Exception:
            pass

    async def seen(self, tg_user_id: int, is_premium: bool | None = None) -> None:
        """Обновить last_seen (+опционально is_premium) на сервере."""
        if self._http is None:
            return
        payload = {"tg_user_id": tg_user_id}
        if is_premium is not None:
            payload["is_premium"] = is_premium
        try:
            async with self._http.post(settings.USERS_SEEN_URL, json=payload) as resp:
                _ = await resp.text()
        except Exception:
            pass