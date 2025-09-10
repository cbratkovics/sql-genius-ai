import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship

from backend.models.base import Base, TimestampMixin, UUIDMixin


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

    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    status = Column(Enum(TenantStatus), default=TenantStatus.TRIAL, nullable=False)
    plan = Column(Enum(TenantPlan), default=TenantPlan.FREE, nullable=False)

    # Contact information
    company_name = Column(String, nullable=True)
    contact_email = Column(String, nullable=False)
    contact_phone = Column(String, nullable=True)
    billing_email = Column(String, nullable=True)

    # Subscription details
    stripe_customer_id = Column(String, nullable=True, unique=True)
    stripe_subscription_id = Column(String, nullable=True)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    subscription_ends_at = Column(DateTime(timezone=True), nullable=True)

    # Usage limits
    monthly_query_limit = Column(Integer, default=3)
    monthly_storage_limit_mb = Column(Integer, default=100)
    max_users = Column(Integer, default=1)
    max_concurrent_queries = Column(Integer, default=1)

    # Features
    features = Column(JSON, default=dict)
    custom_branding = Column(Boolean, default=False)
    api_access = Column(Boolean, default=False)
    advanced_analytics = Column(Boolean, default=False)
    data_export = Column(Boolean, default=False)
    team_collaboration = Column(Boolean, default=False)

    # Security
    encryption_key = Column(String, nullable=True)
    allowed_ip_ranges = Column(JSON, default=list)
    sso_enabled = Column(Boolean, default=False)
    sso_config = Column(JSON, default=dict)

    # Database configuration (for database-per-tenant mode)
    database_name = Column(String, nullable=True)
    database_host = Column(String, nullable=True)
    database_port = Column(Integer, nullable=True)

    # Relationships - comment out if related models don't exist yet
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    queries = relationship(
        "Query", back_populates="tenant", cascade="all, delete-orphan"
    )
    files = relationship("File", back_populates="tenant", cascade="all, delete-orphan")
    api_keys = relationship(
        "APIKey", back_populates="tenant", cascade="all, delete-orphan"
    )
    audit_logs = relationship(
        "AuditLog", back_populates="tenant", cascade="all, delete-orphan"
    )

    # Metadata
    metadata_json = Column(JSON, default=dict)

    def is_active(self) -> bool:
        return self.status == TenantStatus.ACTIVE

    def is_trial_expired(self) -> bool:
        if self.status != TenantStatus.TRIAL or not self.trial_ends_at:
            return False
        return datetime.utcnow() > self.trial_ends_at

    def get_query_limit(self) -> int:
        limits = {
            TenantPlan.FREE: 3,
            TenantPlan.PRO: -1,  # Unlimited
            TenantPlan.ENTERPRISE: -1,  # Unlimited
        }
        return limits.get(self.plan, self.monthly_query_limit)
