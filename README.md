# TGNet MVP

Минимальный телеграм-бот (aiogram v3):
- проверяет подписку на 1..N каналов
- записывает/обновляет юзера в БД (SQLite async)
- общается с внешним API (текст + базовое упоминание о медиа)
- режим техработ через .env

## Запуск

1) `python -m venv .venv && source .venv/bin/activate`
2) `pip install -r requirements.txt`
3) Скопируйте `.env.example` в `.env` и заполните значения.
4) `python -m app.main`

### Примечания
- Для prod переключите `DB_DSN` на Postgres, пример:
  `DB_DSN=postgresql+asyncpg://user:pass@host:5432/dbname`
- Список каналов: `REQUIRED_CHANNELS=@ch1,@ch2,-1001234567`
- Если `MAINTENANCE_MODE=true`, бот отвечает сообщением и не пускает дальше.