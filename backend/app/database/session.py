from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings
from app.core.retry import retry_async

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,
    pool_recycle=settings.DB_POOL_RECYCLE_SECONDS,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT_SECONDS,
    connect_args={
        "timeout": settings.DB_CONNECT_TIMEOUT_SECONDS,
        "command_timeout": settings.DB_COMMAND_TIMEOUT_SECONDS,
    },
)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def ping_database() -> None:
    """Open a connection and run SELECT 1. Raises on failure."""
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1"))


async def wait_for_database(active: Settings | None = None) -> None:
    """Retry database connectivity during process startup."""
    config = active or get_settings()
    await retry_async(
        ping_database,
        attempts=config.DB_CONNECT_ATTEMPTS,
        base_delay=config.DB_CONNECT_RETRY_BASE_SECONDS,
        max_delay=config.DB_CONNECT_RETRY_MAX_SECONDS,
        operation_name="database_connect",
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Request-scoped unit of work. Commits on success, rolls back on error."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
