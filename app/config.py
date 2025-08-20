# app/config.py
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Абсолютный путь к .env в корне проекта
ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT_DIR / ".env"


class Settings(BaseSettings):
    # Общие
    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"
    TZ: str = "Europe/Berlin"

    # Боты
    TELEGRAM_TOKEN: str
    TELEGRAM_CHECKER_TOKEN: Optional[str] = None  # второй бот для проверки подписки

    # API/LLM
    API_URL: str = "http://127.0.0.1:8080/v1/chat"
    LLM_TIMEOUT_SEC: int = 40
    SUPPORT_CHAT_URL: str = "https://t.me/your_support"

    # Подписка
    REQUIRED_CHANNELS: str = ""  # CSV: "@channel1,@channel2,-100123..."
    MAINTENANCE_MODE: bool = False
    MAINTENANCE_MESSAGE: str = "Идут технические работы. Попробуйте позже."

    # БД и сервисные ручки
    DB_DSN: str = "sqlite+aiosqlite:///./data.sqlite3"
    USERS_UPSERT_URL: str = "http://127.0.0.1:8080/v1/users/upsert"
    USERS_SEEN_URL: str = "http://127.0.0.1:8080/v1/users/seen"

    # pydantic-settings сам прочитает .env по абсолютному пути
    model_config = SettingsConfigDict(
        env_file=ENV_PATH.as_posix(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("TELEGRAM_TOKEN")
    @classmethod
    def _validate_main_token(cls, v: str) -> str:
        if ":" not in v:
            raise ValueError("TELEGRAM_TOKEN имеет неверный формат (ожидается 'id:hash').")
        return v

    @field_validator("TELEGRAM_CHECKER_TOKEN")
    @classmethod
    def _validate_checker_token(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v != "" and ":" not in v:
            raise ValueError("TELEGRAM_CHECKER_TOKEN имеет неверный формат (ожидается 'id:hash') или оставьте пустым.")
        return v

    @property
    def required_channels(self) -> List[str]:
        raw = (self.REQUIRED_CHANNELS or "").strip()
        return [p.strip() for p in raw.split(",") if p.strip()]


settings = Settings()