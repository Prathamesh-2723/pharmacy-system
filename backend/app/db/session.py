from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.rls import set_tenant_context

# Check if using sqlite or postgresql
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args=connect_args,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db(tenant_id: Optional[str] = None) -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding an async database session.
    When PostgreSQL RLS is enabled, sets 'app.current_tenant'.
    """
    async with async_session_factory() as session:
        if settings.POSTGRES_RLS_ENABLED and tenant_id:
            try:
                await set_tenant_context(session, tenant_id)
            except Exception:
                # In non-Postgres environments (e.g. SQLite tests), skip quietly
                pass
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
