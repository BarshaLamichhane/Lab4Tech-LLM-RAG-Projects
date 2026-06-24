from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from backend.app.config import CONFIG


DEFAULT_PROVIDER = "mistral"
DEFAULT_MODEL = "mistral-large-latest"
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"


def initialize_llm_settings_database() -> None:
    CONFIG.database_path.parent.mkdir(parents=True, exist_ok=True)
    with _connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_llm_settings (
                username TEXT PRIMARY KEY COLLATE NOCASE,
                provider TEXT NOT NULL DEFAULT 'mistral',
                model_name TEXT NOT NULL DEFAULT 'mistral-large-latest',
                api_key TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )


def get_user_llm_settings(username: str) -> dict:
    initialize_llm_settings_database()
    with _connection() as connection:
        row = connection.execute(
            "SELECT provider, model_name, api_key, updated_at FROM user_llm_settings WHERE username = ?",
            (username,),
        ).fetchone()
    if not row:
        return {
            "provider": DEFAULT_PROVIDER,
            "model_name": DEFAULT_MODEL,
            "has_api_key": False,
            "api_key_preview": "",
            "updated_at": None,
        }
    api_key = row["api_key"] or ""
    return {
        "provider": row["provider"],
        "model_name": row["model_name"],
        "has_api_key": bool(api_key),
        "api_key_preview": _key_preview(api_key),
        "updated_at": row["updated_at"],
    }


def save_user_llm_settings(
    username: str,
    provider: str,
    model_name: str,
    api_key: str | None = None,
    clear_api_key: bool = False,
) -> dict:
    initialize_llm_settings_database()
    provider = provider.strip().lower()
    model_name = model_name.strip()
    if provider not in {"mistral", "openai"}:
        raise ValueError("Provider must be Mistral or OpenAI.")
    if not model_name:
        raise ValueError("Model name is required.")

    existing_key = _existing_api_key(username)
    next_key = None if clear_api_key else (api_key.strip() if api_key and api_key.strip() else existing_key)
    now = datetime.now(UTC).isoformat()
    with _connection() as connection:
        connection.execute(
            """
            INSERT INTO user_llm_settings (username, provider, model_name, api_key, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                provider = excluded.provider,
                model_name = excluded.model_name,
                api_key = excluded.api_key,
                updated_at = excluded.updated_at
            """,
            (username, provider, model_name, next_key, now),
        )
    return get_user_llm_settings(username)


def get_effective_llm_settings(username: str | None) -> dict:
    if not username:
        return {"provider": DEFAULT_PROVIDER, "api_key": None, "model_name": ""}
    initialize_llm_settings_database()
    with _connection() as connection:
        row = connection.execute(
            "SELECT provider, model_name, api_key FROM user_llm_settings WHERE username = ?",
            (username,),
        ).fetchone()
    if not row:
        return {"provider": DEFAULT_PROVIDER, "api_key": None, "model_name": ""}
    return {
        "provider": row["provider"],
        "api_key": row["api_key"],
        "model_name": row["model_name"] or "",
    }


def get_effective_mistral_credentials(username: str | None) -> tuple[str | None, str]:
    settings = get_effective_llm_settings(username)
    if settings["provider"] != "mistral":
        return None, ""
    return settings["api_key"], settings["model_name"]


def _existing_api_key(username: str) -> str | None:
    with _connection() as connection:
        row = connection.execute(
            "SELECT api_key FROM user_llm_settings WHERE username = ?",
            (username,),
        ).fetchone()
    return row["api_key"] if row else None


def _key_preview(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "••••"
    return f"{api_key[:4]}••••{api_key[-4:]}"


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(CONFIG.database_path, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection
