from sqlalchemy import Column, Integer, DateTime, String, Boolean
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.sql import func
from datetime import datetime
from typing import Any
import uuid


@as_declarative()
class Base:
    id: Any
    __name__: str
    
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)


class TenantMixin:
    tenant_id = Column(String, nullable=False, index=True)


class SoftDeleteMixin:
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()


class UUIDMixin:
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))


class AuditMixin:
    created_by = Column(String, nullable=True)
    updated_by = Column(String, nullable=True)
    version = Column(Integer, default=1, nullable=False)