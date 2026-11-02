import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Core settings
    PROJECT_NAME: str = "SQL Genius AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Database - Render provides DATABASE_URL
    DATABASE_URL: str | None = os.getenv("DATABASE_URL")

    # Optional PostgreSQL settings (not needed when using DATABASE_URL)
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_DB: str | None = None
    POSTGRES_HOST: str | None = None
    POSTGRES_PORT: int | None = 5432

    # Security
    SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", "your-secret-key-change-in-production"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 1
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 48
    ENCRYPTION_KEY: str = os.getenv(
        "ENCRYPTION_KEY", "default-encryption-key-change-in-production"
    )

    # CORS
    CORS_ORIGINS: list[str] = [
        o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()
    ] or ["*"]

    # Redis
    REDIS_URL: str | None = os.getenv("REDIS_URL")
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    QUERY_CACHE_TTL_SECONDS: int = 3600
    QUERY_RESULT_CACHE_TTL_SECONDS: int = 3600

    # AI APIs
    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
    ANTHROPIC_TIMEOUT_SECONDS: float = 20.0
    ANTHROPIC_MAX_OUTPUT_TOKENS: int = 700
    OPENAI_API_KEY: str | None = None

    # Stripe (optional for demo)
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None
    STRIPE_PRICE_ID_PRO: str | None = None
    STRIPE_PRICE_ID_ENTERPRISE: str | None = None

    # Optional local/reference backup integration
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    S3_REGION: str = "us-east-1"

    # Email (optional for demo)
    SMTP_HOST: str | None = None
    SMTP_PORT: int | None = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = "noreply@example.com"
    EMAILS_FROM_NAME: str | None = "SQL Genius AI"

    # Admin (optional for demo)
    FIRST_SUPERUSER: str | None = None
    FIRST_SUPERUSER_PASSWORD: str | None = None

    # Features
    ENABLE_DOCS: bool = True
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    class Config:
        case_sensitive = True


settings = Settings()
