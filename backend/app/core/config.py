from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "RAGFlow"
    ENV: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # Auth
    JWT_SECRET: str = "change-me-in-env"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://ragflow:ragflow@postgres:5432/ragflow"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # Object storage (MinIO / S3-compatible)
    S3_ENDPOINT_URL: str = "http://minio:9000"
    S3_ACCESS_KEY: str = "ragflow"
    S3_SECRET_KEY: str = "ragflow123"
    S3_BUCKET: str = "ragflow-documents"

    # LLM providers (Phase 1 uses one default provider; gateway supports more)
    DEFAULT_LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    # Embeddings
    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_DIM: int = 1536

    # Uploads
    MAX_UPLOAD_MB: int = 50
    ALLOWED_UPLOAD_TYPES: list[str] = ["pdf", "docx", "pptx", "txt", "md", "csv", "xlsx", "html"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
