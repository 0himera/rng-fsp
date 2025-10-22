from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import EnvSettingsSource


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

    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["*"])
    cors_allow_credentials: bool = Field(default=True)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @staticmethod
    def _parse_csv(value: Any) -> list[str] | Any:
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",") if item.strip()]
            return items or ["*"]
        return value

    @field_validator("cors_allow_origins", "cors_allow_methods", "cors_allow_headers", mode="before")
    @classmethod
    def _prepare_list_fields(cls, value: Any) -> list[str] | Any:
        return cls._parse_csv(value)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls,
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        class LenientEnvSettingsSource(EnvSettingsSource):
            def decode_complex_value(self, field_name, field, value):
                try:
                    return super().decode_complex_value(field_name, field, value)
                except ValueError:
                    return value

        def lenient_env_settings(settings_cls=settings_cls):
            source = LenientEnvSettingsSource(settings_cls)
            return source()

        return (
            init_settings,
            lenient_env_settings,
            dotenv_settings,
            file_secret_settings,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
