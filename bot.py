import os
import asyncio
import aiohttp
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.types import Message
from dotenv import load_dotenv, find_dotenv

print("CWD:", os.getcwd())
env_path = find_dotenv()
print("find_dotenv() ->", env_path)
load_dotenv(env_path)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = os.getenv("API_URL", "http://127.0.0.1:8080/v1/chat")
if not TELEGRAM_TOKEN or ":" not in TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN не найден/некорректен")

# ====== Бот ======
bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
_http: Optional[aiohttp.ClientSession] = None

@dp.message(CommandStart())
async def start_cmd(message: Message):
    await message.answer("Привет! Напиши вопрос — отвечу через GPT API.")

@dp.message()
async def handle_message(message: Message):
    global _http
    q = (message.text or "").strip()
    if not q:
        await message.answer("Напиши текст вопроса.")
        return

    # Логируем вопрос в терминал (вместо отправки в чат)
    print(f"[{message.from_user.id}] {q}")

    # Индикатор
    typing_msg = await message.answer("Печатаю…")

    payload = {
        "session_id": str(message.from_user.id),  # можно оставить для совместимости
        "input": q,
        "use_memory": False
    }
    try:
        assert _http is not None
        async with _http.post(API_URL, json=payload, timeout=aiohttp.ClientTimeout(total=40)) as resp:
            txt = await resp.text()
            if resp.status != 200:
                print("API ERROR:", resp.status, txt)
                raise RuntimeError(f"API {resp.status}: {txt}")
            data = await resp.json()
            answer = data.get("text") or str(data)
    except Exception as e:
        answer = f"Ошибка при запросе API: {e}"
    finally:
        try:
            await typing_msg.delete()
        except Exception:
            pass

    # Разбиваем длинные ответы и не режем <pre><code>
    limit = 3900
    text = answer
    while text:
        chunk = text[:limit]
        await message.answer(chunk, disable_web_page_preview=True)
        text = text[len(chunk):]

async def main():
    global _http
    _http = aiohttp.ClientSession()
    try:
        # снимаем вебхук — иначе конфликт с polling
        await bot.delete_webhook(drop_pending_updates=False)
        await dp.start_polling(bot)
    finally:
        await _http.close()

if __name__ == "__main__":
    asyncio.run(main())