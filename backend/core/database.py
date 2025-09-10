import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from backend.core.config import settings
from backend.models.base import Base
from typing import AsyncGenerator
import asyncio

# Set up logging
logger = logging.getLogger(__name__)


def transform_database_url(url: str) -> str:
    """
    Transform database URL to use async drivers.
    
    Handles:
    - PostgreSQL: postgresql:// -> postgresql+asyncpg://
    - SQLite: sqlite:/// -> sqlite+aiosqlite:///
    """
    if not url:
        # Default to async SQLite for local development
        return "sqlite+aiosqlite:///./sql_genius.db"
    
    # Handle Render.com PostgreSQL URLs
    if url.startswith("postgres://"):
        # Render uses the old postgres:// format, convert to postgresql://
        url = url.replace("postgres://", "postgresql://", 1)
    
    # Convert to async PostgreSQL driver
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        logger.info("Using asyncpg driver for PostgreSQL")
    
    # Convert to async SQLite driver
    elif url.startswith("sqlite:///"):
        url = url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        logger.info("Using aiosqlite driver for SQLite")
    
    return url


# Transform the database URL for async compatibility
database_url = transform_database_url(settings.DATABASE_URL)

# Determine if we're using SQLite
is_sqlite = "sqlite" in database_url

# Configure engine with production-ready settings
if is_sqlite:
    # SQLite configuration
    engine = create_async_engine(
        database_url,
        echo=settings.ENVIRONMENT == "development",
        poolclass=NullPool,  # SQLite doesn't support connection pooling well
    )
else:
    # PostgreSQL configuration with connection pooling
    engine = create_async_engine(
        database_url,
        echo=settings.ENVIRONMENT == "development",
        # Connection pool settings for production
        poolclass=QueuePool,
        pool_size=20,  # Number of persistent connections
        max_overflow=10,  # Maximum overflow connections
        pool_timeout=30,  # Timeout for getting connection from pool
        pool_recycle=3600,  # Recycle connections after 1 hour
        pool_pre_ping=True,  # Test connections before using
        # Additional settings for reliability
        connect_args={
            "server_settings": {"jit": "off"},
            "command_timeout": 60,
            "timeout": 30,
        } if not is_sqlite else {},
    )

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    Includes retry logic for connection failures.
    """
    retry_count = 0
    max_retries = 3
    
    while retry_count < max_retries:
        try:
            async with AsyncSessionLocal() as session:
                yield session
                break
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                logger.error(f"Failed to get database session after {max_retries} retries: {e}")
                raise
            logger.warning(f"Database connection attempt {retry_count} failed, retrying...")
            await asyncio.sleep(1 * retry_count)  # Exponential backoff


async def create_tables():
    """Create all database tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


async def drop_tables():
    """Drop all database tables."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


async def check_database_connection():
    """
    Check if database connection is working.
    Useful for health checks.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


class TenantAwareSession:
    """Wrapper for tenant-aware database operations."""
    
    def __init__(self, session: AsyncSession, tenant_id: str):
        self.session = session
        self.tenant_id = tenant_id
    
    def query(self, model):
        base_query = self.session.query(model)
        if hasattr(model, 'tenant_id'):
            return base_query.filter(model.tenant_id == self.tenant_id)
        return base_query
    
    async def add(self, obj):
        if hasattr(obj, 'tenant_id') and not obj.tenant_id:
            obj.tenant_id = self.tenant_id
        self.session.add(obj)
    
    async def commit(self):
        await self.session.commit()
    
    async def rollback(self):
        await self.session.rollback()
    
    async def close(self):
        await self.session.close()


async def get_tenant_db(tenant_id: str) -> AsyncGenerator[TenantAwareSession, None]:
    """Get tenant-aware database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield TenantAwareSession(session, tenant_id)
        finally:
            await session.close()


# Log the database URL (without credentials) on startup
if database_url:
    # Hide credentials in log
    safe_url = database_url.split('@')[-1] if '@' in database_url else database_url
    logger.info(f"Database configured: ...@{safe_url}")