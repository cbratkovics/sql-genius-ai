from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from backend.models.base import Base, TimestampMixin, UUIDMixin, TenantMixin
import enum


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    USER = "user"
    VIEWER = "viewer"


class User(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "users"
    
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    
    # Profile information
    avatar_url = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    department = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    
    # Authentication
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    last_login_ip = Column(String, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    
    # Preferences
    preferences = Column(JSON, default=dict)
    timezone = Column(String, default="UTC")
    language = Column(String, default="en")
    
    # API access
    api_key_hash = Column(String, nullable=True)
    api_key_created_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    queries = relationship("Query", back_populates="user", cascade="all, delete-orphan")
    saved_queries = relationship("SavedQuery", back_populates="user", cascade="all, delete-orphan")
    # dashboards = relationship("Dashboard", back_populates="user", cascade="all, delete-orphan")  # Model doesn't exist yet
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    # Usage tracking
    total_queries = Column(Integer, default=0)
    queries_this_month = Column(Integer, default=0)
    last_query_at = Column(DateTime(timezone=True), nullable=True)
    
    # Permissions cache
    permissions = Column(JSON, default=list)
    
    def can_access_tenant(self, tenant_id: str) -> bool:
        return self.is_superuser or self.tenant_id == tenant_id
    
    def has_permission(self, permission: str) -> bool:
        if self.is_superuser:
            return True
        return permission in self.permissions
    
    def is_tenant_admin(self) -> bool:
        return self.role in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]