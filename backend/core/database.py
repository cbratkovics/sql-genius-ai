from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from backend.core.config import settings
from backend.models.base import Base
from typing import AsyncGenerator
import asyncio


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    poolclass=NullPool if "sqlite" in settings.DATABASE_URL else None,
    pool_pre_ping=True,
    pool_recycle=300,
)

AsyncSessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class TenantAwareSession:
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
    async with AsyncSessionLocal() as session:
        try:
            yield TenantAwareSession(session, tenant_id)
        finally:
            await session.close()