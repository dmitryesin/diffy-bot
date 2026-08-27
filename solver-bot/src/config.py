from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str
    solver_api_url: str

    request_timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0
    max_retry_delay: float = 10.0

    max_calculation_points: int = 100_000

    default_method: str = "runge_kutta"
    default_rounding: str = "4"
    default_language: str = "en"
    default_hints: str = "true"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
