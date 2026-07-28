from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


# Import models here to register them with DeclarativeBase metadata
from app.models import tenancy, documents, chat


async def get_db() -> AsyncSession:
    """FastAPI dependency. Yields a scoped async session per request."""
    async with AsyncSessionLocal() as session:
        yield session
