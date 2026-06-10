from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SESSIONS_PATH = PROJECT_ROOT / "data" / "user_sessions.json"


def save_user_session(username: str, session_type: str, title: str, payload: dict) -> dict:
    sessions = _load_sessions()
    session = {
        "id": str(uuid4()),
        "username": username,
        "session_type": session_type,
        "title": title,
        "created_at": datetime.now(UTC).isoformat(),
        "payload": payload,
    }
    sessions.append(session)
    _save_sessions(sessions)
    return session


def load_user_sessions(username: str) -> list[dict]:
    return [
        session
        for session in reversed(_load_sessions())
        if session.get("username") == username
    ]


def _load_sessions() -> list[dict]:
    if not SESSIONS_PATH.exists():
        return []
    return json.loads(SESSIONS_PATH.read_text(encoding="utf-8"))


def _save_sessions(sessions: list[dict]) -> None:
    SESSIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SESSIONS_PATH.write_text(json.dumps(sessions, indent=2), encoding="utf-8")
