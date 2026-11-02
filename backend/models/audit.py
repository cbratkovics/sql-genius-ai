from __future__ import annotations

import enum
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TenantMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from backend.models.tenant import Tenant
    from backend.models.user import User


class AuditEventType(str, enum.Enum):
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    
    QUERY_EXECUTED = "query_executed"
    QUERY_FAILED = "query_failed"
    
    FILE_UPLOADED = "file_uploaded"
    FILE_DOWNLOADED = "file_downloaded"
    FILE_DELETED = "file_deleted"
    
    DATA_EXPORTED = "data_exported"
    DATA_ACCESSED = "data_accessed"
    
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPDATED = "subscription_updated"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    
    SETTINGS_CHANGED = "settings_changed"
    PERMISSIONS_CHANGED = "permissions_changed"
    
    SECURITY_VIOLATION = "security_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class AuditSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLog(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "audit_logs"
    
    # Event details
    event_type: Mapped[AuditEventType] = mapped_column(Enum(AuditEventType), nullable=False, index=True)
    severity: Mapped[AuditSeverity] = mapped_column(Enum(AuditSeverity), default=AuditSeverity.LOW, nullable=False)
    
    # User and session info
    user_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"), nullable=True, index=True)
    session_id: Mapped[str | None] = mapped_column(String, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Event data
    resource_type: Mapped[str | None] = mapped_column(String, nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    action: Mapped[str] = mapped_column(String, nullable=False)
    
    # Details
    description: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=True)
    
    # Request/Response info
    request_path: Mapped[str | None] = mapped_column(String, nullable=True)
    request_method: Mapped[str | None] = mapped_column(String, nullable=True)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Timing
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Data integrity
    data_hash: Mapped[str] = mapped_column(String, nullable=False)
    
    # Compliance flags
    contains_pii: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    requires_retention: Mapped[bool] = mapped_column(Boolean, default=True, nullable=True)
    compliance_tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=True)
    
    # Relationships
    user: Mapped[User | None] = relationship("User", back_populates="audit_logs")
    tenant: Mapped[Tenant | None] = relationship("Tenant", back_populates="audit_logs")
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "description": self.description,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "duration_ms": self.duration_ms,
            "contains_pii": self.contains_pii
        }


class APIKey(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "api_keys"
    
    name: Mapped[str] = mapped_column(String, nullable=False)
    key_hash: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # Permissions and limits
    permissions: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=True)
    rate_limit_per_hour: Mapped[int] = mapped_column(Integer, default=1000, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=True)
    
    # Security
    allowed_ip_ranges: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped[User] = relationship("User", back_populates="api_keys")
    tenant: Mapped[Tenant | None] = relationship("Tenant", back_populates="api_keys")
    
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            # SQLite returns naive values for timezone columns; they store UTC.
            expires_at = expires_at.replace(tzinfo=UTC)
        return datetime.now(UTC) > expires_at
    
    def can_access_ip(self, ip_address: str) -> bool:
        if not self.allowed_ip_ranges:
            return True
        
        from backend.services.security import security_service
        return security_service.validate_ip_access(ip_address, self.allowed_ip_ranges)