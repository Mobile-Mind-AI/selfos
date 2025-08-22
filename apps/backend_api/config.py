"""
Configuration management for SelfOS Backend API.

This module provides centralized configuration management using Pydantic BaseSettings,
which automatically loads values from environment variables with type validation.
"""

from functools import lru_cache

from pydantic import Field, PostgresDsn, validator
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    url: PostgresDsn = Field(
        default="postgresql://selfos:selfos@localhost:5432/selfos",
        env="DATABASE_URL",
        description="PostgreSQL database URL",
    )

    # Connection pool settings
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    pool_recycle: int = Field(default=3600, env="DB_POOL_RECYCLE")

    # Query settings
    echo_queries: bool = Field(default=False, env="DB_ECHO_QUERIES")

    class Config:
        env_prefix = "DB_"
        extra = "ignore"


class RedisSettings(BaseSettings):
    """Redis configuration settings."""

    url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL",
        description="Redis connection URL",
    )

    # Connection settings
    max_connections: int = Field(default=20, env="REDIS_MAX_CONNECTIONS")
    retry_on_timeout: bool = Field(default=True, env="REDIS_RETRY_ON_TIMEOUT")
    health_check_interval: int = Field(default=30, env="REDIS_HEALTH_CHECK_INTERVAL")

    class Config:
        env_prefix = "REDIS_"
        extra = "ignore"


class SecuritySettings(BaseSettings):
    """Security and authentication configuration."""

    # JWT settings
    jwt_secret_key: str = Field(
        default="your-secret-key-change-in-production",
        env="JWT_SECRET_KEY",
        description="Secret key for JWT token signing",
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=1440, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )  # 24 hours

    # Firebase settings
    firebase_credentials_path: str | None = Field(
        default=None,
        env="GOOGLE_APPLICATION_CREDENTIALS",
        description="Path to Firebase service account JSON file",
    )
    firebase_project_id: str | None = Field(default=None, env="FIREBASE_PROJECT_ID")

    # Rate limiting
    rate_limit_requests_per_minute: int = Field(
        default=120, env="RATE_LIMIT_REQUESTS_PER_MINUTE"
    )
    rate_limit_requests_per_hour: int = Field(default=2000, env="RATE_LIMIT_PER_HOUR")
    rate_limit_burst_limit: int = Field(default=50, env="RATE_LIMIT_BURST")

    # CORS settings
    cors_origins: list[str] = Field(
        default=["*"], env="CORS_ORIGINS", description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")

    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_prefix = "SECURITY_"
        extra = "ignore"


class AISettings(BaseSettings):
    """AI providers and services configuration."""

    # OpenAI settings
    openai_api_key: str | None = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-3.5-turbo", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=1000, env="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.7, env="OPENAI_TEMPERATURE")

    # Anthropic settings
    anthropic_api_key: str | None = Field(default=None, env="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(
        default="claude-3-sonnet-20240229", env="ANTHROPIC_MODEL"
    )
    anthropic_max_tokens: int = Field(default=1000, env="ANTHROPIC_MAX_TOKENS")

    # AI service settings
    default_provider: str = Field(default="openai", env="AI_DEFAULT_PROVIDER")
    request_timeout: int = Field(default=30, env="AI_REQUEST_TIMEOUT")
    max_retries: int = Field(default=3, env="AI_MAX_RETRIES")

    # Memory/Vector DB settings
    vector_db_provider: str = Field(
        default="local", env="VECTOR_DB_PROVIDER"
    )  # local, pinecone, weaviate
    pinecone_api_key: str | None = Field(default=None, env="PINECONE_API_KEY")
    pinecone_environment: str | None = Field(default=None, env="PINECONE_ENVIRONMENT")

    # Memory settings from .env
    memory_similarity_threshold: float = Field(
        default=0.7, env="MEMORY_SIMILARITY_THRESHOLD"
    )
    memory_max_content_length: int = Field(
        default=2000, env="MEMORY_MAX_CONTENT_LENGTH"
    )

    class Config:
        env_prefix = "AI_"
        extra = "ignore"


class EmailSettings(BaseSettings):
    """Email service configuration."""

    # SMTP settings
    smtp_host: str = Field(default="localhost", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: str | None = Field(default=None, env="SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, env="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, env="SMTP_USE_TLS")
    smtp_use_ssl: bool = Field(default=False, env="SMTP_USE_SSL")

    # Email settings
    from_email: str = Field(default="noreply@selfos.ai", env="FROM_EMAIL")
    from_name: str = Field(default="SelfOS", env="FROM_NAME")

    # Template settings
    templates_dir: str = Field(default="email_templates", env="EMAIL_TEMPLATES_DIR")

    class Config:
        env_prefix = "EMAIL_"
        extra = "ignore"


class LoggingSettings(BaseSettings):
    """Logging configuration."""

    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", env="LOG_FORMAT"
    )

    # File logging
    log_to_file: bool = Field(default=False, env="LOG_TO_FILE")
    log_file_path: str = Field(default="logs/app.log", env="LOG_FILE_PATH")
    log_file_max_size: int = Field(default=10485760, env="LOG_FILE_MAX_SIZE")  # 10MB
    log_file_backup_count: int = Field(default=5, env="LOG_FILE_BACKUP_COUNT")

    # Structured logging
    json_format: bool = Field(default=False, env="LOG_JSON_FORMAT")

    class Config:
        env_prefix = "LOG_"
        extra = "ignore"


class AppSettings(BaseSettings):
    """Main application settings."""

    # Application metadata
    app_name: str = Field(default="SelfOS Backend API", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    app_description: str = Field(
        default="Backend API for SelfOS - Personal Life Management System",
        env="APP_DESCRIPTION",
    )

    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    testing: bool = Field(default=False, env="TESTING")

    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    reload: bool = Field(default=False, env="RELOAD")
    workers: int = Field(default=1, env="WORKERS")

    # API settings
    api_prefix: str = Field(default="/api", env="API_PREFIX")
    docs_url: str | None = Field(default="/docs", env="DOCS_URL")
    redoc_url: str | None = Field(default="/redoc", env="REDOC_URL")
    openapi_url: str | None = Field(default="/openapi.json", env="OPENAPI_URL")

    # File upload settings
    max_file_size: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    allowed_file_types: list[str] = Field(
        default=["image/jpeg", "image/png", "image/gif", "video/mp4", "audio/mpeg"],
        env="ALLOWED_FILE_TYPES",
    )
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")

    @validator("allowed_file_types", pre=True)
    def parse_file_types(cls, v):
        if isinstance(v, str):
            return [file_type.strip() for file_type in v.split(",")]
        return v

    # Feature flags
    enable_registration: bool = Field(default=True, env="ENABLE_REGISTRATION")
    enable_social_login: bool = Field(default=True, env="ENABLE_SOCIAL_LOGIN")
    enable_email_verification: bool = Field(
        default=False, env="ENABLE_EMAIL_VERIFICATION"
    )
    enable_ai_features: bool = Field(default=True, env="ENABLE_AI_FEATURES")
    enable_storytelling: bool = Field(default=True, env="ENABLE_STORYTELLING")
    enable_notifications: bool = Field(default=True, env="ENABLE_NOTIFICATIONS")

    # Event system settings
    event_system_enabled: bool = Field(default=True, env="EVENT_SYSTEM_ENABLED")
    event_timeout_seconds: int = Field(default=30, env="EVENT_TIMEOUT_SECONDS")

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def is_testing(self) -> bool:
        return self.testing or self.environment.lower() == "testing"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class Settings(BaseSettings):
    """Main settings class that combines all configuration sections."""

    app: AppSettings = AppSettings()
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    security: SecuritySettings = SecuritySettings()
    ai: AISettings = AISettings()
    email: EmailSettings = EmailSettings()
    logging: LoggingSettings = LoggingSettings()

    def get_database_url(self) -> str:
        """Get the database URL as a string."""
        return str(self.database.url)

    def get_redis_url(self) -> str:
        """Get the Redis URL as a string."""
        return self.redis.url

    def get_cors_origins(self) -> list[str]:
        """Get CORS origins list."""
        return self.security.cors_origins

    def get_rate_limit_config(self) -> dict[str, int]:
        """Get rate limiting configuration."""
        return {
            "requests_per_minute": self.security.rate_limit_requests_per_minute,
            "requests_per_hour": self.security.rate_limit_requests_per_hour,
            "burst_limit": self.security.rate_limit_burst_limit,
        }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    """
    Get application settings with caching.

    Uses lru_cache to ensure settings are loaded only once and reused.
    This is the recommended pattern for FastAPI settings.
    """
    return Settings()


# Export commonly used settings for convenience
settings = get_settings()
