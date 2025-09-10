import os
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Core settings
    PROJECT_NAME: str = "SQL Genius AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database - Render provides DATABASE_URL
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

    # Optional PostgreSQL settings (not needed when using DATABASE_URL)
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: Optional[int] = 5432

    # Security
    SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", "your-secret-key-change-in-production"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ENCRYPTION_KEY: str = os.getenv(
        "ENCRYPTION_KEY", "default-encryption-key-change-in-production"
    )

    # CORS
    CORS_ORIGINS: List[str] = [
        o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()
    ] or ["*"]

    # Redis
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")

    # AI APIs
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY: Optional[str] = None

    # Stripe (optional for demo)
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRICE_ID_PRO: Optional[str] = None
    STRIPE_PRICE_ID_ENTERPRISE: Optional[str] = None

    # Email (optional for demo)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = "noreply@example.com"
    EMAILS_FROM_NAME: Optional[str] = "SQL Genius AI"

    # Admin (optional for demo)
    FIRST_SUPERUSER: Optional[str] = None
    FIRST_SUPERUSER_PASSWORD: Optional[str] = None

    # Features
    ENABLE_DOCS: bool = True
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    class Config:
        case_sensitive = True


settings = Settings()
