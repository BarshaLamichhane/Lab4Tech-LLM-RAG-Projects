from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from uuid import uuid4

from backend.app.config import CONFIG


def initialize_session_database() -> None:
    CONFIG.database_path.parent.mkdir(parents=True, exist_ok=True)
    with _connection() as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                session_type TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT,
                status TEXT NOT NULL DEFAULT 'completed',
                payload TEXT NOT NULL
            )
            """
        )
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(user_sessions)").fetchall()
        }
        if "updated_at" not in columns:
            connection.execute("ALTER TABLE user_sessions ADD COLUMN updated_at TEXT")
        if "status" not in columns:
            connection.execute(
                "ALTER TABLE user_sessions ADD COLUMN status TEXT NOT NULL DEFAULT 'completed'"
            )
        connection.execute(
            "UPDATE user_sessions SET updated_at = created_at WHERE updated_at IS NULL"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_username_created "
            "ON user_sessions(username, created_at DESC)"
        )


def save_user_session(username: str, session_type: str, title: str, payload: dict) -> dict:
    initialize_session_database()
    session = {
        "id": str(uuid4()),
        "username": username,
        "session_type": session_type,
        "title": title,
        "created_at": datetime.now(UTC).isoformat(),
        "status": "completed",
        "payload": payload,
    }
    session["updated_at"] = session["created_at"]
    with _connection() as connection:
        connection.execute(
            """
            INSERT INTO user_sessions
                (id, username, session_type, title, created_at, updated_at, status, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session["id"],
                username,
                session_type,
                title,
                session["created_at"],
                session["updated_at"],
                session["status"],
                json.dumps(payload),
            ),
        )
    return session


def save_interview_session(
    username: str,
    title: str,
    payload: dict,
    status: str = "in_progress",
    session_id: str | None = None,
) -> dict:
    initialize_session_database()
    now = datetime.now(UTC).isoformat()
    if session_id:
        with _connection() as connection:
            existing = connection.execute(
                "SELECT id, created_at FROM user_sessions WHERE id = ? AND username = ?",
                (session_id, username),
            ).fetchone()
            if not existing:
                raise ValueError("Interview session not found")
            connection.execute(
                """
                UPDATE user_sessions
                SET title = ?, updated_at = ?, status = ?, payload = ?
                WHERE id = ? AND username = ?
                """,
                (title, now, status, json.dumps(payload), session_id, username),
            )
        created_at = existing["created_at"]
    else:
        session_id = str(uuid4())
        created_at = now
        with _connection() as connection:
            connection.execute(
                """
                INSERT INTO user_sessions
                    (id, username, session_type, title, created_at, updated_at, status, payload)
                VALUES (?, ?, 'interview_practice', ?, ?, ?, ?, ?)
                """,
                (session_id, username, title, created_at, now, status, json.dumps(payload)),
            )
    return {
        "id": session_id,
        "username": username,
        "session_type": "interview_practice",
        "title": title,
        "created_at": created_at,
        "updated_at": now,
        "status": status,
        "payload": payload,
    }


def load_interview_sessions(username: str) -> list[dict]:
    return [
        session
        for session in load_user_sessions(username)
        if session["session_type"] == "interview_practice"
    ]


def load_adaptive_interview_sessions(username: str) -> list[dict]:
    return [
        session
        for session in load_user_sessions(username)
        if session["session_type"] == "adaptive_interview"
    ]


def load_interview_session(username: str, session_id: str) -> dict:
    initialize_session_database()
    with _connection() as connection:
        row = connection.execute(
            """
            SELECT id, username, session_type, title, created_at, updated_at, status, payload
            FROM user_sessions
            WHERE id = ? AND username = ? AND session_type = 'interview_practice'
            """,
            (session_id, username),
        ).fetchone()
    if not row:
        raise ValueError("Interview session not found")
    return _session_from_row(row)


def load_user_sessions(username: str) -> list[dict]:
    initialize_session_database()
    with _connection() as connection:
        rows = connection.execute(
            """
            SELECT id, username, session_type, title, created_at, updated_at, status, payload
            FROM user_sessions
            WHERE username = ?
            ORDER BY updated_at DESC
            """,
            (username,),
        ).fetchall()
    return [_session_from_row(row) for row in rows]


def _session_from_row(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "username": row["username"],
        "session_type": row["session_type"],
        "title": row["title"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"] or row["created_at"],
        "status": row["status"],
        "payload": json.loads(row["payload"]),
    }


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(CONFIG.database_path, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection
