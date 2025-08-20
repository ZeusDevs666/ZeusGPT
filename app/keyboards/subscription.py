from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def make_sub_keyboard(channels: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for ch in channels:
        url = f"https://t.me/{ch.lstrip('@')}" if ch.startswith("@") else None
        if url:
            rows.append([InlineKeyboardButton(text=f"Подписаться: {ch}", url=url)])
    rows.append([InlineKeyboardButton(text="Проверить подписку", callback_data="check_sub")])
    return InlineKeyboardMarkup(inline_keyboard=rows)