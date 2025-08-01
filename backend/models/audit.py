from sqlalchemy import Column, String, Text, DateTime, JSON, Enum, Boolean, Integer
from sqlalchemy.orm import relationship
from backend.models.base import Base, TimestampMixin, UUIDMixin, TenantMixin
import enum
from datetime import datetime


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
    event_type = Column(Enum(AuditEventType), nullable=False, index=True)
    severity = Column(Enum(AuditSeverity), default=AuditSeverity.LOW, nullable=False)
    
    # User and session info
    user_id = Column(String, nullable=True, index=True)
    session_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    # Event data
    resource_type = Column(String, nullable=True)  # e.g., "query", "file", "user"
    resource_id = Column(String, nullable=True, index=True)
    action = Column(String, nullable=False)  # e.g., "create", "read", "update", "delete"
    
    # Details
    description = Column(Text, nullable=False)
    details = Column(JSON, default=dict)  # Additional event-specific data
    
    # Request/Response info
    request_path = Column(String, nullable=True)
    request_method = Column(String, nullable=True)
    response_status = Column(Integer, nullable=True)
    
    # Timing
    duration_ms = Column(Integer, nullable=True)
    
    # Data integrity
    data_hash = Column(String, nullable=False)  # Hash of event data for integrity
    
    # Compliance flags
    contains_pii = Column(Boolean, default=False)
    requires_retention = Column(Boolean, default=True)
    compliance_tags = Column(JSON, default=list)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    tenant = relationship("Tenant", back_populates="audit_logs")
    
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
    
    name = Column(String, nullable=False)
    key_hash = Column(String, unique=True, nullable=False, index=True)
    
    user_id = Column(String, nullable=False, index=True)
    
    # Permissions and limits
    permissions = Column(JSON, default=list)
    rate_limit_per_hour = Column(Integer, default=1000)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Security
    allowed_ip_ranges = Column(JSON, default=list)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    tenant = relationship("Tenant", back_populates="api_keys")
    
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def can_access_ip(self, ip_address: str) -> bool:
        if not self.allowed_ip_ranges:
            return True
        
        from backend.services.security import security_service
        return security_service.validate_ip_access(ip_address, self.allowed_ip_ranges)