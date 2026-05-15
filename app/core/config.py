from enum import Enum
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Mode(Enum):
    DEV = "DEV"
    PROD = "PROD"


class Settings(BaseSettings):
    MODE: Mode = Mode.DEV  # Application mode, can be DEV or PROD
    DEBUG: bool  # Debug mode for the application
    POSTGRES_PORT: int  # PostgreSQL port for the application
    POSTGRES_HOST: str  # PostgreSQL host for the application
    POSTGRES_USER: str  # PostgreSQL user for the application
    POSTGRES_PASSWORD: str  # Password for the PostgreSQL user
    POSTGRES_DB: str  # Database name for the application
    SECRET_KEY: str  # Secret key for the application, used for signing tokens and cookies
    ADMIN_USERNAME: str  # Admin username for the application
    ADMIN_PASSWORD: str  # Admin credentials for the application
    CORS_ALLOWED_ORIGINS: str  # Comma-separated list of allowed origins for CORS
    SSO_CLIENT_URL: str  # URL of the SSO client service
    SSO_CLIENT_ID: str  # Username for the SSO client
    SSO_CLIENT_SECRET: str  # Password for the SSO client
    GATEWAY_CLIENT_URL: str  # URL of the Gateway client service
    GATEWAY_CLIENT_ID: str  # Username for the Gateway client
    GATEWAY_CLIENT_SECRET: str  # Password for the Gateway client
    GATEWAY_CLIENT_GRANT_TYPE: str = "password"  # Grant type for the Gateway client
    ACCESS_TOKEN_EXPIRE_MINUTES: int = (
        60  # Expiration time for access tokens in minutes
    )
    KAFKA_BOOTSTRAP_SERVERS: str  # Kafka bootstrap servers
    REDIS_URL: str  # Redis URL for caching and session management
    MINIO_HOST: str  # MinIO host for file storage
    MINIO_PORT: int  # MinIO port for file storage
    MINIO_ACCESS_KEY: str  # MinIO access key for file storage
    MINIO_SECRET_KEY: str  # MinIO secret key for file storage
    KAFKA_USERNAME: str  # Kafka username for authentication
    KAFKA_PASSWORD: str  # Kafka password for authentication
    INTERNAL_USERNAME: str
    INTERNAL_PASSWORD: str
    REDIS_HOST: str  # Redis host for job scheduling
    REDIS_PORT: int  # Redis port for job scheduling
    REDIS_PASSWORD: str  # Redis password for job scheduling
    REDIS_DB: int  # Redis database for job scheduling
    INTERNAL_API_KEY: str = "internal-service-secret-key-2026"
    TRIP_SERVICE_INTERNAL_URL: str = "https://xizmatdev.imv.uz/api/v1/trip"
    APP_MODE: str

    # Trip Service
    TRIP_SERVICE_HOST: str
    TRIP_SERVICE_PORT: str
    TRIP_SERVICE_USER: str
    TRIP_SERVICE_PASSWORD: str

    # Telegram bot settings
    API_TOKEN: str
    CHAT_ID: int

    # DATABASE_URL is a computed property that constructs the database URL
    @property
    def DATABASE_URL(self):
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),  # ✅ full path
        extra="ignore",
    )


settings = Settings()
