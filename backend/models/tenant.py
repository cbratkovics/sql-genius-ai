from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from backend.models.audit import APIKey, AuditLog
    from backend.models.file import File
    from backend.models.query import Query
    from backend.models.user import User


class TenantStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"


class TenantPlan(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Tenant(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    status: Mapped[TenantStatus] = mapped_column(Enum(TenantStatus), default=TenantStatus.TRIAL, nullable=False)
    plan: Mapped[TenantPlan] = mapped_column(Enum(TenantPlan), default=TenantPlan.FREE, nullable=False)

    # Contact information
    company_name: Mapped[str | None] = mapped_column(String, nullable=True)
    contact_email: Mapped[str] = mapped_column(String, nullable=False)
    contact_phone: Mapped[str | None] = mapped_column(String, nullable=True)
    billing_email: Mapped[str | None] = mapped_column(String, nullable=True)

    # Subscription details
    stripe_customer_id: Mapped[str | None] = mapped_column(String, nullable=True, unique=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String, nullable=True)
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    subscription_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Usage limits
    monthly_query_limit: Mapped[int] = mapped_column(Integer, default=3, nullable=True)
    monthly_storage_limit_mb: Mapped[int] = mapped_column(Integer, default=100, nullable=True)
    max_users: Mapped[int] = mapped_column(Integer, default=1, nullable=True)
    max_concurrent_queries: Mapped[int] = mapped_column(Integer, default=1, nullable=True)

    # Features
    features: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=True)
    custom_branding: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    api_access: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    advanced_analytics: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    data_export: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    team_collaboration: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)

    # Security
    encryption_key: Mapped[str | None] = mapped_column(String, nullable=True)
    allowed_ip_ranges: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=True)
    sso_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    sso_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=True)

    # Database configuration (for database-per-tenant mode)
    database_name: Mapped[str | None] = mapped_column(String, nullable=True)
    database_host: Mapped[str | None] = mapped_column(String, nullable=True)
    database_port: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships - comment out if related models don't exist yet
    users: Mapped[list[User]] = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    queries: Mapped[list[Query]] = relationship(
        "Query", back_populates="tenant", cascade="all, delete-orphan"
    )
    files: Mapped[list[File]] = relationship("File", back_populates="tenant", cascade="all, delete-orphan")
    api_keys: Mapped[list[APIKey]] = relationship(
        "APIKey", back_populates="tenant", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(
        "AuditLog", back_populates="tenant", cascade="all, delete-orphan"
    )

    # Metadata
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=True)

    def is_active(self) -> bool:
        return self.status == TenantStatus.ACTIVE

    def is_trial_expired(self) -> bool:
        if self.status != TenantStatus.TRIAL or not self.trial_ends_at:
            return False
        expires_at = self.trial_ends_at
        if expires_at.tzinfo is None:
            # SQLite returns naive values for timezone columns; they store UTC.
            expires_at = expires_at.replace(tzinfo=UTC)
        return datetime.now(UTC) > expires_at

    def get_query_limit(self) -> int:
        limits = {
            TenantPlan.FREE: 3,
            TenantPlan.PRO: -1,  # Unlimited
            TenantPlan.ENTERPRISE: -1,  # Unlimited
        }
        return limits.get(self.plan, self.monthly_query_limit)
