from __future__ import annotations

import os
from dataclasses import dataclass

from backend.app.llm_context import get_current_llm_username
from backend.app.llm_settings_store import (
    DEFAULT_MODEL,
    DEFAULT_OPENAI_MODEL,
    get_effective_llm_settings,
)
from backend.job_description.job_description_cleaner_mistral_api import (
    MISTRAL_API_TIMEOUT_MS,
    get_mistral_client,
)


@dataclass(frozen=True)
class LLMJsonResponse:
    content: str
    provider: str
    model: str


def effective_llm_provider_model() -> tuple[str, str]:
    settings = get_effective_llm_settings(get_current_llm_username())
    provider = settings["provider"]
    if provider == "openai":
        return provider, settings["model_name"] or os.getenv("OPENAI_MODEL_NAME", DEFAULT_OPENAI_MODEL)
    return provider, settings["model_name"] or os.getenv("MISTRAL_API_MODEL_NAME", DEFAULT_MODEL)


def complete_json_chat(system_prompt: str, user_prompt: str, temperature: float = 0.0) -> LLMJsonResponse:
    settings = get_effective_llm_settings(get_current_llm_username())
    provider = settings["provider"]
    if provider == "openai":
        return _complete_openai_json_chat(settings, system_prompt, user_prompt, temperature)
    return _complete_mistral_json_chat(settings, system_prompt, user_prompt, temperature)


def _complete_mistral_json_chat(
    settings: dict,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
) -> LLMJsonResponse:
    api_key = settings.get("api_key") or os.getenv("MISTRAL_API_KEY")
    model = settings.get("model_name") or os.getenv("MISTRAL_API_MODEL_NAME", DEFAULT_MODEL)
    response = get_mistral_client(api_key).chat.complete(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    return LLMJsonResponse(
        content=response.choices[0].message.content,
        provider="mistral",
        model=model,
    )


def _complete_openai_json_chat(
    settings: dict,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
) -> LLMJsonResponse:
    api_key = settings.get("api_key") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found. Add your OpenAI key in Account settings or .env.")
    try:
        from openai import OpenAI
    except ModuleNotFoundError as exc:
        raise RuntimeError("OpenAI provider requires the openai package. Add it to requirements and install dependencies.") from exc

    model = settings.get("model_name") or os.getenv("OPENAI_MODEL_NAME", DEFAULT_OPENAI_MODEL)
    response = OpenAI(api_key=api_key, timeout=MISTRAL_API_TIMEOUT_MS / 1000).chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    return LLMJsonResponse(
        content=response.choices[0].message.content or "{}",
        provider="openai",
        model=model,
    )
