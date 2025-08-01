from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, JSON, Enum, Text
from sqlalchemy.orm import relationship
from backend.models.base import Base, TimestampMixin, UUIDMixin, TenantMixin, SoftDeleteMixin
import enum


class FileStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    ARCHIVED = "archived"


class FileType(str, enum.Enum):
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    PARQUET = "parquet"


class File(Base, UUIDMixin, TimestampMixin, TenantMixin, SoftDeleteMixin):
    __tablename__ = "files"
    
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_type = Column(Enum(FileType), nullable=False)
    mime_type = Column(String, nullable=True)
    
    # Storage
    storage_path = Column(String, nullable=True)  # S3 or local path
    file_size_bytes = Column(Integer, nullable=False)
    file_hash = Column(String, nullable=False)  # SHA256 hash
    
    # Processing
    status = Column(Enum(FileStatus), default=FileStatus.PENDING)
    processing_error = Column(Text, nullable=True)
    
    # Metadata
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=list)
    
    # Data profile
    row_count = Column(Integer, nullable=True)
    column_count = Column(Integer, nullable=True)
    columns_metadata = Column(JSON, nullable=True)  # Column names, types, stats
    data_sample = Column(JSON, nullable=True)  # First 5 rows
    
    # Security
    is_encrypted = Column(Boolean, default=True)
    encryption_key_id = Column(String, nullable=True)
    access_control = Column(JSON, default=dict)
    contains_pii = Column(Boolean, default=False)
    data_classification = Column(String, nullable=True)
    
    # Relationships
    queries = relationship("Query", back_populates="file")
    
    # Retention
    expires_at = Column(DateTime(timezone=True), nullable=True)
    auto_delete = Column(Boolean, default=True)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "file_type": self.file_type.value,
            "file_size_bytes": self.file_size_bytes,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns_metadata": self.columns_metadata
        }