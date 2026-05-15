from collections.abc import AsyncGenerator
from typing import Callable

from core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# create an async engine
engine = create_async_engine(url=settings.DATABASE_URL, echo=settings.DEBUG)
session_factory: Callable[[], AsyncSession] = async_sessionmaker(engine)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async dependency for getting database session
    """
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
