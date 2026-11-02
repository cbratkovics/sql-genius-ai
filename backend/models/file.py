from __future__ import annotations

import enum
from datetime import datetime
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

from backend.models.base import (
    Base,
    SoftDeleteMixin,
    TenantMixin,
    TimestampMixin,
    UUIDMixin,
)

if TYPE_CHECKING:
    from backend.models.query import Query
    from backend.models.tenant import Tenant
    from backend.models.user import User


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
    
    filename: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[FileType] = mapped_column(Enum(FileType), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Storage
    storage_path: Mapped[str | None] = mapped_column(String, nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    file_hash: Mapped[str] = mapped_column(String, nullable=False)
    
    # Processing
    status: Mapped[FileStatus] = mapped_column(Enum(FileStatus), default=FileStatus.PENDING, nullable=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Metadata
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=True)
    
    # Data profile
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    columns_metadata: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    data_sample: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    
    # Security
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=True)
    encryption_key_id: Mapped[str | None] = mapped_column(String, nullable=True)
    access_control: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=True)
    contains_pii: Mapped[bool] = mapped_column(Boolean, default=False, nullable=True)
    data_classification: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Relationships
    user: Mapped[User] = relationship("User", foreign_keys=[user_id])
    tenant: Mapped[Tenant | None] = relationship("Tenant", back_populates="files")
    queries: Mapped[list[Query]] = relationship("Query", back_populates="file")
    
    # Retention
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_delete: Mapped[bool] = mapped_column(Boolean, default=True, nullable=True)
    
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