from __future__ import annotations

from contextvars import ContextVar


_CURRENT_USERNAME: ContextVar[str | None] = ContextVar("current_llm_username", default=None)


def set_current_llm_username(username: str | None) -> None:
    _CURRENT_USERNAME.set(username)


def get_current_llm_username() -> str | None:
    return _CURRENT_USERNAME.get()
