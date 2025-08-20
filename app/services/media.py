from aiogram import Bot
from aiogram.types import PhotoSize, Document, Video, Voice, VideoNote, Audio
from typing import Any, Dict, Tuple, Optional

async def download_file(bot: Bot, file_id: str) -> Tuple[bytes, Dict[str, Any]]:
    f = await bot.get_file(file_id)
    data = await bot.download_file(f.file_path)
    content = await data.read()
    meta = {
        "file_path": f.file_path,
        "file_size": f.file_size,
    }
    return content, meta

def pick_best_photo(photos: list[PhotoSize]) -> Optional[PhotoSize]:
    return max(photos, key=lambda p: p.file_size or 0) if photos else None

def detect_media_kind(message) -> str | None:
    if message.photo: return "photo"
    if message.document: return "document"
    if message.video: return "video"
    if message.voice: return "voice"
    if message.audio: return "audio"
    if message.video_note: return "video_note"
    return None