from typing import Literal, Self
from urllib.parse import unquote, urlparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENVIRONMENT: Literal["local", "production"] = "local"
    SECRET_KEY: str
    DEBUG: bool
    ALLOWED_HOSTS: list[str]
    LANGUAGE_CODE: str
    TIME_ZONE: str

    DATABASE_URL: str | None = None
    SECURE_SSL_REDIRECT: bool = True
    SESSION_COOKIE_SECURE: bool = True
    CSRF_COOKIE_SECURE: bool = True
    SECURE_HSTS_SECONDS: int = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS: bool = True
    SECURE_HSTS_PRELOAD: bool = True
    SECURE_PROXY_SSL_HEADER_NAME: str | None = "HTTP_X_FORWARDED_PROTO"
    SECURE_PROXY_SSL_HEADER_VALUE: str | None = "https"
    SECURE_REFERRER_POLICY: str = "same-origin"
    LOGIN_RATELIMIT_LIMIT: int = 5
    LOGIN_RATELIMIT_PERIOD: int = 60  # seconds

    @model_validator(mode="after")
    def validate_environment(self) -> Self:
        if self.ENVIRONMENT == "production" and self.DEBUG:
            msg = "DEBUG must be False when ENVIRONMENT=production."
            raise ValueError(msg)
        if self.ENVIRONMENT == "production" and not self.DATABASE_URL:
            msg = "DATABASE_URL is required when ENVIRONMENT=production."
            raise ValueError(msg)
        return self

    def database_config(self) -> dict[str, str | int]:
        if not self.DATABASE_URL:
            msg = "DATABASE_URL is not configured."
            raise ValueError(msg)

        parsed = urlparse(self.DATABASE_URL)
        scheme = parsed.scheme.replace("+", "")

        if scheme in {"postgres", "postgresql"}:
            engine = "django.db.backends.postgresql"
        elif scheme == "sqlite":
            engine = "django.db.backends.sqlite3"
        else:
            msg = f"Unsupported database scheme: {parsed.scheme}"
            raise ValueError(msg)

        if engine == "django.db.backends.sqlite3":
            return {
                "ENGINE": engine,
                "NAME": parsed.path.lstrip("/") or ":memory:",
            }

        if not parsed.hostname or not parsed.path:
            msg = "DATABASE_URL must include host and database name."
            raise ValueError(msg)

        config: dict[str, str | int] = {
            "ENGINE": engine,
            "NAME": parsed.path.lstrip("/"),
            "USER": unquote(parsed.username or ""),
            "PASSWORD": unquote(parsed.password or ""),
            "HOST": parsed.hostname,
            "PORT": parsed.port or 5432,
        }

        return config


settings = Settings()
