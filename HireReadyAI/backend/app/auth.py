from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Lock
from time import monotonic

import jwt
from fastapi import Header, HTTPException, Request

from backend.app.config import CONFIG
from backend.app.llm_context import set_current_llm_username


PASSWORD_ITERATIONS = 600_000
MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 15 * 60
_LOGIN_ATTEMPTS: dict[str, list[float]] = {}
_ATTEMPT_LOCK = Lock()
_DUMMY_PASSWORD_HASH: str | None = None


@dataclass(frozen=True)
class CurrentUser:
    id: int
    username: str
    role: str
    token_version: int


def initialize_auth_database() -> None:
    _ensure_user_table()
    with _connection() as connection:
        user_count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    if user_count == 0:
        if not CONFIG.initial_admin_password:
            raise RuntimeError(
                "No users exist. Set INITIAL_ADMIN_PASSWORD to bootstrap the first admin."
            )
        create_user(
            CONFIG.initial_admin_username,
            CONFIG.initial_admin_password,
            role="admin",
        )


def _ensure_user_table() -> None:
    CONFIG.database_path.parent.mkdir(parents=True, exist_ok=True)
    with _connection() as connection:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'user')),
                active INTEGER NOT NULL DEFAULT 1,
                token_version INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(users)").fetchall()
        }
        if "token_version" not in columns:
            connection.execute(
                "ALTER TABLE users ADD COLUMN token_version INTEGER NOT NULL DEFAULT 1"
            )


def create_user(username: str, password: str, role: str = "user") -> CurrentUser:
    _ensure_user_table()
    normalized_username = username.strip()
    _validate_credentials(normalized_username, password, role)
    try:
        with _connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (username, password_hash, role, active, token_version, created_at)
                VALUES (?, ?, ?, 1, 1, ?)
                """,
                (
                    normalized_username,
                    hash_password(password),
                    role,
                    datetime.now(UTC).isoformat(),
                ),
            )
            return CurrentUser(
                id=cursor.lastrowid,
                username=normalized_username,
                role=role,
                token_version=1,
            )
    except sqlite3.IntegrityError as exc:
        raise ValueError(f"User '{normalized_username}' already exists") from exc


def authenticate(username: str, password: str, client_key: str) -> CurrentUser:
    _check_rate_limit(client_key)
    with _connection() as connection:
        row = connection.execute(
            "SELECT id, username, password_hash, role, active, token_version FROM users WHERE username = ?",
            (username.strip(),),
        ).fetchone()

    password_hash = row["password_hash"] if row else _dummy_password_hash()
    password_matches = verify_password(password, password_hash)
    if not row or not row["active"] or not password_matches:
        _record_failed_attempt(client_key)
        raise HTTPException(status_code=401, detail="Invalid username or password")

    _clear_attempts(client_key)
    user = CurrentUser(
        id=row["id"],
        username=row["username"],
        role=row["role"],
        token_version=row["token_version"],
    )
    set_current_llm_username(user.username)
    return user


def create_access_token(user: CurrentUser) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user.id),
            "username": user.username,
            "ver": user.token_version,
            "iat": now,
            "exp": now + timedelta(minutes=CONFIG.access_token_minutes),
            "iss": CONFIG.jwt_issuer,
        },
        CONFIG.jwt_secret,
        algorithm="HS256",
    )


def require_user(
    request: Request,
    authorization: str | None = Header(default=None),
) -> CurrentUser:
    token = request.cookies.get(CONFIG.auth_cookie_name)
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Login required")

    try:
        payload = jwt.decode(
            token,
            CONFIG.jwt_secret,
            algorithms=["HS256"],
            issuer=CONFIG.jwt_issuer,
        )
        user_id = int(payload["sub"])
        token_version = int(payload["ver"])
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired login") from exc

    with _connection() as connection:
        row = connection.execute(
            "SELECT id, username, role, active, token_version FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    if not row or not row["active"] or row["token_version"] != token_version:
        raise HTTPException(status_code=401, detail="User is inactive or unavailable")
    return CurrentUser(
        id=row["id"],
        username=row["username"],
        role=row["role"],
        token_version=row["token_version"],
    )


def change_password(user: CurrentUser, current_password: str, new_password: str) -> None:
    _validate_password(new_password)
    with _connection() as connection:
        row = connection.execute(
            "SELECT password_hash FROM users WHERE id = ?",
            (user.id,),
        ).fetchone()
        if not row or not verify_password(current_password, row["password_hash"]):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        connection.execute(
            """
            UPDATE users
            SET password_hash = ?, token_version = token_version + 1
            WHERE id = ?
            """,
            (hash_password(new_password), user.id),
        )


def reset_user_password(username: str, new_password: str) -> None:
    _validate_password(new_password)
    with _connection() as connection:
        cursor = connection.execute(
            """
            UPDATE users
            SET password_hash = ?, token_version = token_version + 1
            WHERE username = ?
            """,
            (hash_password(new_password), username.strip()),
        )
    if cursor.rowcount != 1:
        raise ValueError(f"User '{username.strip()}' was not found")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_ITERATIONS,
    )
    return "$".join(
        (
            "pbkdf2_sha256",
            str(PASSWORD_ITERATIONS),
            base64.urlsafe_b64encode(salt).decode("ascii"),
            base64.urlsafe_b64encode(digest).decode("ascii"),
        )
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            base64.urlsafe_b64decode(salt),
            int(iterations),
        )
        return hmac.compare_digest(base64.urlsafe_b64encode(digest).decode("ascii"), expected)
    except (TypeError, ValueError):
        return False


def _validate_credentials(username: str, password: str, role: str) -> None:
    if len(username) < 3 or len(username) > 80:
        raise ValueError("Username must contain between 3 and 80 characters")
    _validate_password(password)
    if role not in {"admin", "user"}:
        raise ValueError("Role must be admin or user")


def _validate_password(password: str) -> None:
    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters")


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(CONFIG.database_path, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def _dummy_password_hash() -> str:
    global _DUMMY_PASSWORD_HASH
    if _DUMMY_PASSWORD_HASH is None:
        _DUMMY_PASSWORD_HASH = hash_password("not-a-real-user-password")
    return _DUMMY_PASSWORD_HASH


def _check_rate_limit(client_key: str) -> None:
    now = monotonic()
    with _ATTEMPT_LOCK:
        recent = [
            attempt
            for attempt in _LOGIN_ATTEMPTS.get(client_key, [])
            if now - attempt < LOGIN_WINDOW_SECONDS
        ]
        _LOGIN_ATTEMPTS[client_key] = recent
        if len(recent) >= MAX_LOGIN_ATTEMPTS:
            raise HTTPException(status_code=429, detail="Too many login attempts. Try again later.")


def _record_failed_attempt(client_key: str) -> None:
    with _ATTEMPT_LOCK:
        _LOGIN_ATTEMPTS.setdefault(client_key, []).append(monotonic())


def _clear_attempts(client_key: str) -> None:
    with _ATTEMPT_LOCK:
        _LOGIN_ATTEMPTS.pop(client_key, None)
