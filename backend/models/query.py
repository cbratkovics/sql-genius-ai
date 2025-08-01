from sqlalchemy import Column, String, Text, Integer, Float, Boolean, ForeignKey, JSON, Enum, Index
from sqlalchemy.orm import relationship
from backend.models.base import Base, TimestampMixin, UUIDMixin, TenantMixin
import enum


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
    natural_language_query = Column(Text, nullable=False)
    generated_sql = Column(Text, nullable=True)
    executed_sql = Column(Text, nullable=True)
    
    # Metadata
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    file_id = Column(String, ForeignKey("files.id"), nullable=True)
    dataset_name = Column(String, nullable=True)
    query_type = Column(Enum(QueryType), default=QueryType.NATURAL_LANGUAGE)
    status = Column(Enum(QueryStatus), default=QueryStatus.PENDING)
    
    # Execution details
    execution_time_ms = Column(Integer, nullable=True)
    rows_returned = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # AI details
    ai_model = Column(String, default="claude-3-sonnet")
    ai_confidence_score = Column(Float, nullable=True)
    ai_explanation = Column(Text, nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    
    # Results
    result_preview = Column(JSON, nullable=True)  # First 10 rows
    result_cache_key = Column(String, nullable=True)
    visualizations = Column(JSON, default=list)
    insights = Column(JSON, default=dict)
    
    # Security
    is_sensitive = Column(Boolean, default=False)
    access_control = Column(JSON, default=dict)
    data_classification = Column(String, nullable=True)
    
    # Performance
    query_complexity_score = Column(Float, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="queries")
    tenant = relationship("Tenant", back_populates="queries")
    file = relationship("File", back_populates="queries")
    
    # Cache control
    cache_hit = Column(Boolean, default=False)
    cached_until = Column(DateTime(timezone=True), nullable=True)
    
    # Audit
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
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
    
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    natural_language_template = Column(Text, nullable=False)
    sql_template = Column(Text, nullable=False)
    
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    category = Column(String, nullable=True)
    tags = Column(JSON, default=list)
    
    # Parameters for template
    parameters = Column(JSON, default=dict)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Sharing
    is_public = Column(Boolean, default=False)
    shared_with_users = Column(JSON, default=list)
    shared_with_teams = Column(JSON, default=list)
    
    # Relationships
    user = relationship("User", back_populates="saved_queries")