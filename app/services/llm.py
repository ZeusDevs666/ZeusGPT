import aiohttp
from typing import Optional
from ..config import settings

class LLMClient:
    def __init__(self):
        self._http: Optional[aiohttp.ClientSession] = None

    async def start(self):
        if not self._http:
            timeout = aiohttp.ClientTimeout(total=settings.LLM_TIMEOUT_SEC)
            self._http = aiohttp.ClientSession(timeout=timeout)

    async def close(self):
        if self._http:
            await self._http.close()
            self._http = None

    async def ask_text(self, user_id: int, text: str) -> str:
        assert self._http is not None
        payload = {
            "session_id": str(user_id),
            "input": text,
            "use_memory": False
        }
        async with self._http.post(settings.API_URL, json=payload) as resp:
            # читаем текст ВСЕГДА для логов
            raw = await resp.text()
            if resp.status != 200:
                raise RuntimeError(f"API {resp.status}: {raw}")
            try:
                data = await resp.json()
                return data.get("text") or str(data)
            except Exception:
                # если сервер вернул не-JSON, покажем сырой текст
                return raw