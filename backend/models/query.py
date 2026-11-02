from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base, TenantMixin, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from backend.models.file import File
    from backend.models.tenant import Tenant
    from backend.models.user import User


class QueryStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueryType(str, enum.Enum):
    NATURAL_LANGUAGE = "natural_language"
    RAW_SQL = "raw_sql"
    SAVED_QUERY = "saved_query"
    SCHEDULED = "scheduled"


class Query(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "queries"
    __table_args__ = (
        Index('idx_tenant_user_status', 'tenant_id', 'user_id', 'status'),
        Index('idx_created_at_desc', 'created_at'),
    )
    
    # User input
    natural_language_query: Mapped[str] = mapped_column(Text, nullable=False)
    generated_sql: Mapped[str | None] = mapped_column(Text, nullable=True)
    executed_sql: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Metadata
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    file_id: Mapped[str | None] = mapped_column(String, ForeignKey("files.id"), nullable=True)
    dataset_name: Mapped[str | None] = mapped_column(String, nullable=True)
    query_type: Mapped[QueryType] = mapped_column(Enum(QueryType), default=QueryType.NATURAL_LANGUAGE, nullable=True)
    status: Mapped[QueryStatus] = mapped_column(Enum(QueryStatus), default=QueryStatus.PENDING, nullable=True)
    
    # Execution details
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rows_returned: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # AI details
    ai_model: Mapped[str] = mapped_column(String, default="claude-3-sonnet", nullable=True)
    ai_confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # Results
    result_preview: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    result_cache_key: Mapped[str | None] = mapped_column(String, nullable=True)
    visualizations: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=True)
    insights: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=True)
    
    # Security
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    access_control: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=True)
    data_classification: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Performance
    query_complexity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Relationships
    user: Mapped[User] = relationship("User", back_populates="queries")
    tenant: Mapped[Tenant | None] = relationship("Tenant", back_populates="queries")
    file: Mapped[File | None] = relationship("File", back_populates="queries")
    
    # Cache control
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    cached_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Audit
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String, nullable=True)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "natural_language_query": self.natural_language_query,
            "generated_sql": self.generated_sql,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "execution_time_ms": self.execution_time_ms,
            "rows_returned": self.rows_returned,
            "error_message": self.error_message,
            "insights": self.insights,
            "visualizations": self.visualizations
        }


class SavedQuery(Base, UUIDMixin, TimestampMixin, TenantMixin):
    __tablename__ = "saved_queries"
    
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    natural_language_template: Mapped[str] = mapped_column(Text, nullable=False)
    sql_template: Mapped[str] = mapped_column(Text, nullable=False)
    
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=True)
    
    # Parameters for template
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=True)
    
    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Sharing
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    shared_with_users: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=True)
    shared_with_teams: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=True)
    
    # Relationships
    user: Mapped[User | None] = relationship("User", back_populates="saved_queries")