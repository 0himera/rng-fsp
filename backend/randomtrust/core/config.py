from functools import lru_cache
from pathlib import Path

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="RandomTrust RNG Backend")
    app_version: str = Field(default="0.1.0")
    api_prefix: str = Field(default="/api")
    environment: str = Field(default="development")

    postgres_host: str = Field(default="postgres")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="randomtrust")
    postgres_user: str = Field(default="randomtrust")
    postgres_password: str = Field(default="randomtrust")
    database_url: AnyUrl = Field(
        default="postgresql+asyncpg://randomtrust:randomtrust@postgres:5432/randomtrust"
    )

    redis_url: AnyUrl = Field(default="redis://redis:6379/0")
    redis_stream_entropy: str = Field(default="entropy:events")
    redis_stream_results: str = Field(default="entropy:results")

    minio_endpoint: AnyUrl = Field(default="http://minio:9000")
    minio_access_key: str = Field(default="randomtrust")
    minio_secret_key: str = Field(default="randomtrustsecret")
    minio_bucket: str = Field(default="entropy-artifacts")

    rng_export_path: Path = Field(default=Path("/data/runs"))

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
