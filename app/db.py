from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from .config import settings

engine = create_async_engine(settings.DB_DSN, echo=False, future=True, pool_pre_ping=True)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

async def init_db():
    # для MVP — создаём таблицы без Alembic
    from .models import User
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)