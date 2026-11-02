from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TenantMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from backend.models.audit import APIKey, AuditLog
    from backend.models.query import Query, SavedQuery
    from backend.models.tenant import Tenant


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    USER = "user"
    VIEWER = "viewer"


class User(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, nullable=False)
    
    # Profile information
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String, nullable=True)
    department: Mapped[str | None] = mapped_column(String, nullable=True)
    job_title: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Authentication
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_ip: Mapped[str | None] = mapped_column(String, nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=True)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Preferences
    preferences: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=True)
    timezone: Mapped[str] = mapped_column(String, default="UTC", nullable=True)
    language: Mapped[str] = mapped_column(String, default="en", nullable=True)
    
    # API access
    api_key_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    api_key_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant: Mapped[Tenant | None] = relationship("Tenant", back_populates="users")
    queries: Mapped[list[Query]] = relationship("Query", back_populates="user", cascade="all, delete-orphan")
    saved_queries: Mapped[list[SavedQuery]] = relationship("SavedQuery", back_populates="user", cascade="all, delete-orphan")
    # dashboards = relationship("Dashboard", back_populates="user", cascade="all, delete-orphan")  # Model doesn't exist yet
    api_keys: Mapped[list[APIKey]] = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    audit_logs: Mapped[list[AuditLog]] = relationship("AuditLog", back_populates="user")
    
    # Usage tracking
    total_queries: Mapped[int] = mapped_column(Integer, default=0, nullable=True)
    queries_this_month: Mapped[int] = mapped_column(Integer, default=0, nullable=True)
    last_query_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Permissions cache
    permissions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=True)
    
    def can_access_tenant(self, tenant_id: str) -> bool:
        return self.is_superuser or self.tenant_id == tenant_id
    
    def has_permission(self, permission: str) -> bool:
        if self.is_superuser:
            return True
        return permission in (self.permissions or [])
    
    def is_tenant_admin(self) -> bool:
        return self.role in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]