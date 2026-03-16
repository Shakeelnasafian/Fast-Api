from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


DEFAULT_AUTH_SECRET = "change-this-secret-before-production"


def _get_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    return int(raw_value)


def _get_list(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw_value = os.getenv(name)
    if raw_value is None or not raw_value.strip():
        return default

    return tuple(item.strip() for item in raw_value.split(",") if item.strip())


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str
    app_version: str
    environment: str
    debug: bool
    database_url: str
    sql_echo: bool
    allowed_origins: tuple[str, ...]
    trusted_hosts: tuple[str, ...]
    auth_secret: str
    access_token_expire_minutes: int
    docs_enabled: bool
    log_level: str


@lru_cache
def get_settings() -> Settings:
    environment = os.getenv("ENVIRONMENT", "development").strip().lower()
    debug = _get_bool("DEBUG", environment != "production")

    return Settings(
        app_name=os.getenv("APP_NAME", "Car Sharing API"),
        app_version=os.getenv("APP_VERSION", "1.0.0"),
        environment=environment,
        debug=debug,
        database_url=os.getenv("DATABASE_URL", "sqlite:///cars.db"),
        sql_echo=_get_bool("SQL_ECHO", False),
        allowed_origins=_get_list(
            "ALLOWED_ORIGINS",
            ("http://localhost:8000", "http://localhost:8080"),
        ),
        trusted_hosts=_get_list(
            "TRUSTED_HOSTS",
            ("localhost", "127.0.0.1", "testserver"),
        ),
        auth_secret=os.getenv("AUTH_SECRET", DEFAULT_AUTH_SECRET),
        access_token_expire_minutes=_get_int("ACCESS_TOKEN_EXPIRE_MINUTES", 60),
        docs_enabled=_get_bool("ENABLE_DOCS", environment != "production"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
