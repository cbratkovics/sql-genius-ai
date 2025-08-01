from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator
import secrets


class Settings(BaseSettings):
    PROJECT_NAME: str = "SQL Genius AI"
    VERSION: str = "2.0.0"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    
    DATABASE_URL: Optional[str] = None
    
    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if isinstance(v, str):
            return v
        return f"postgresql+asyncpg://{values.data.get('POSTGRES_USER')}:{values.data.get('POSTGRES_PASSWORD')}@{values.data.get('POSTGRES_HOST')}:{values.data.get('POSTGRES_PORT')}/{values.data.get('POSTGRES_DB')}"
    
    REDIS_URL: str = "redis://localhost:6379"
    
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: Optional[str] = None
    
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PRICE_ID_PRO: str
    STRIPE_PRICE_ID_ENTERPRISE: str
    
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8501"]
    
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    @field_validator("EMAILS_FROM_NAME", mode="before")
    def get_project_name(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if not v:
            return values.data.get("PROJECT_NAME", "SQL Genius AI")
        return v
    
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 48
    
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str
    
    USERS_OPEN_REGISTRATION: bool = True
    
    SENTRY_DSN: Optional[str] = None
    
    MAX_FILE_SIZE_MB: int = 200
    ALLOWED_FILE_EXTENSIONS: list[str] = [".csv", ".xlsx", ".xls"]
    
    QUERY_CACHE_TTL_SECONDS: int = 3600
    QUERY_RESULT_CACHE_TTL_SECONDS: int = 300
    
    FREE_TIER_QUERY_LIMIT: int = 3
    PRO_TIER_QUERY_LIMIT: int = -1  # Unlimited
    ENTERPRISE_TIER_QUERY_LIMIT: int = -1  # Unlimited
    
    TENANT_ISOLATION_MODE: str = "schema"  # Options: "database", "schema", "row"
    
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    ENCRYPTION_KEY: str = secrets.token_urlsafe(32)
    
    S3_BUCKET_NAME: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_REGION: str = "us-east-1"
    
    ENABLE_DOCS: bool = True
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()