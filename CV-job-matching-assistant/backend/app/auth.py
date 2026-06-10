from __future__ import annotations

import os
import secrets
from dataclasses import dataclass

from fastapi import Header, HTTPException


@dataclass(frozen=True)
class CurrentUser:
    username: str
    role: str


_TOKENS: dict[str, CurrentUser] = {}


def login(username: str, password: str) -> tuple[str, CurrentUser]:
    users = {
        os.getenv("APP_ADMIN_USERNAME", "admin"): (
            os.getenv("APP_ADMIN_PASSWORD", "admin123"),
            "admin",
        ),
        os.getenv("APP_USER_USERNAME", "user"): (
            os.getenv("APP_USER_PASSWORD", "user123"),
            "user",
        ),
    }
    expected = users.get(username)
    if not expected or not secrets.compare_digest(password, expected[0]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    user = CurrentUser(username=username, role=expected[1])
    token = secrets.token_urlsafe(32)
    _TOKENS[token] = user
    return token, user


def require_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Login required")

    user = _TOKENS.get(authorization.removeprefix("Bearer ").strip())
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired login")
    return user
