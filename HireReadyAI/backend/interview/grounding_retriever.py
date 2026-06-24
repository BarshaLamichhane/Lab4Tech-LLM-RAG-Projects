from __future__ import annotations

from backend.interview.grounding_index import (
    retrieve_grounding_context as retrieve_faiss_context,
)
from backend.interview.schemas import InterviewContext, InterviewQuestion


MAX_CONTEXT_ITEMS = 5
MAX_CONTEXT_CHARS = 6000


def retrieve_grounding_context(
    question: InterviewQuestion,
    context: InterviewContext | None,
) -> tuple[list[str], list[str]]:
    """Retrieve evaluation evidence from the shared persistent FAISS index."""
    del context
    query = question.grounding_query or " ".join(
        value for value in [question.skill, question.question] if value
    )
    try:
        retrieved = retrieve_faiss_context(query, top_k=MAX_CONTEXT_ITEMS)
    except ValueError:
        return [], []

    contexts: list[str] = []
    sources: list[str] = []
    for item in retrieved:
        text = str(item.get("text", "")).strip()
        source = str(item.get("source", "unknown")).strip() or "unknown"
        if text:
            contexts.append(text[:MAX_CONTEXT_CHARS])
            if source not in sources:
                sources.append(source)
    return contexts, sources
