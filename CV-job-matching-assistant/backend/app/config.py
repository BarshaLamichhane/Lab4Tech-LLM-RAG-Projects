from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _boolean(name: str, default: bool) -> bool:
    value = os.getenv(name)
    return default if value is None else value.lower() in {"1", "true", "yes", "on"}


def _origins() -> list[str]:
    configured = os.getenv("CORS_ALLOWED_ORIGINS")
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]
    return [
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


@dataclass(frozen=True)
class AppConfig:
    environment: str
    database_path: Path
    jwt_secret: str
    jwt_issuer: str
    access_token_minutes: int
    auth_cookie_name: str
    cookie_secure: bool
    cookie_samesite: str
    cors_allowed_origins: list[str]
    allowed_hosts: list[str]
    api_docs_enabled: bool
    code_execution_enabled: bool
    max_upload_bytes: int
    initial_admin_username: str
    initial_admin_password: str | None

    @property
    def production(self) -> bool:
        return self.environment == "production"


def load_config() -> AppConfig:
    environment = os.getenv("APP_ENV", "development").lower()
    production = environment == "production"
    database_path = Path(os.getenv("DATABASE_PATH", PROJECT_ROOT / "data" / "app.db"))
    jwt_secret = os.getenv("JWT_SECRET", "development-only-change-me")
    cookie_samesite = os.getenv("COOKIE_SAMESITE", "lax").lower()
    access_token_minutes = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
    max_upload_bytes = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
    cors_allowed_origins = _origins()
    allowed_hosts = [
        host.strip()
        for host in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
        if host.strip()
    ]

    if production and len(jwt_secret) < 32:
        raise RuntimeError("JWT_SECRET must contain at least 32 characters in production")
    if production and ("*" in cors_allowed_origins or "*" in allowed_hosts):
        raise RuntimeError("Wildcard CORS origins and allowed hosts are not permitted in production")
    if cookie_samesite not in {"lax", "strict", "none"}:
        raise RuntimeError("COOKIE_SAMESITE must be lax, strict, or none")
    if production and cookie_samesite == "none" and not _boolean("COOKIE_SECURE", True):
        raise RuntimeError("COOKIE_SECURE must be true when COOKIE_SAMESITE=none")
    if access_token_minutes <= 0 or max_upload_bytes <= 0:
        raise RuntimeError("ACCESS_TOKEN_MINUTES and MAX_UPLOAD_BYTES must be positive")

    return AppConfig(
        environment=environment,
        database_path=database_path,
        jwt_secret=jwt_secret,
        jwt_issuer=os.getenv("JWT_ISSUER", "hire-ready-ai"),
        access_token_minutes=access_token_minutes,
        auth_cookie_name=os.getenv("AUTH_COOKIE_NAME", "hire_ready_session"),
        cookie_secure=_boolean("COOKIE_SECURE", production),
        cookie_samesite=cookie_samesite,
        cors_allowed_origins=cors_allowed_origins,
        allowed_hosts=allowed_hosts,
        api_docs_enabled=_boolean("API_DOCS_ENABLED", not production),
        code_execution_enabled=_boolean("CODE_EXECUTION_ENABLED", not production),
        max_upload_bytes=max_upload_bytes,
        initial_admin_username=os.getenv("INITIAL_ADMIN_USERNAME", "admin"),
        initial_admin_password=os.getenv("INITIAL_ADMIN_PASSWORD"),
    )


CONFIG = load_config()
