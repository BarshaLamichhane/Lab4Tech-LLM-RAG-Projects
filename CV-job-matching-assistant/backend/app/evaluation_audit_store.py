from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from uuid import uuid4

from backend.app.config import CONFIG


def initialize_evaluation_audit_database() -> None:
    CONFIG.database_path.parent.mkdir(parents=True, exist_ok=True)
    with _connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluation_audits (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                question_id TEXT NOT NULL,
                model TEXT NOT NULL,
                created_at TEXT NOT NULL,
                prompt TEXT NOT NULL,
                raw_response TEXT NOT NULL,
                evaluation TEXT NOT NULL
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_evaluation_audits_username_created "
            "ON evaluation_audits(username, created_at DESC)"
        )


def save_evaluation_audit(
    username: str,
    question_id: str,
    model: str,
    prompt: str,
    raw_response: str,
    evaluation: dict,
) -> str:
    initialize_evaluation_audit_database()
    audit_id = str(uuid4())
    with _connection() as connection:
        connection.execute(
            """
            INSERT INTO evaluation_audits
                (id, username, question_id, model, created_at, prompt, raw_response, evaluation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                audit_id,
                username,
                question_id,
                model,
                datetime.now(UTC).isoformat(),
                prompt,
                raw_response,
                json.dumps(evaluation),
            ),
        )
    return audit_id


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(CONFIG.database_path, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection
