from __future__ import annotations

import json
import time

from backend.interview.schemas import InterviewQuestion, PreparationInterviewResponse
from backend.job_description.job_description_cleaner_mistral_api import (
    MISTRAL_API_MODEL_NAME,
    get_mistral_client,
)


def generate_preparation_interview(
    role: str,
    selected_skills: list[str],
    question_count: int = 5,
    level: str = "intermediate",
) -> PreparationInterviewResponse:
    if not selected_skills:
        raise ValueError("Select at least one skill for preparation mode.")

    question_count = max(1, min(question_count, 20))
    prompt = f"""
You are a technical interview coach.

Generate a preparation interview question set.

Return ONLY valid JSON:
{{
  "questions": [
    {{
      "id": "q1",
      "question": "...",
      "question_type": "technical",
      "difficulty": "easy|medium|hard",
      "skill": "...",
      "source_group": "selected_skills",
      "expected_points": ["..."],
      "follow_up_questions": ["exactly one follow-up question"],
      "scoring_rubric": ["..."]
    }}
  ]
}}

Role: {role}
Level: {level}
Selected skills: {json.dumps(selected_skills, ensure_ascii=False)}
Question count: {question_count}

Rules:
- Generate exactly {question_count} questions.
- Generate questions only for selected skills.
- If skill is Python, generate Python coding/concept questions.
- If skill is SQL, generate SQL query questions.
- If skill is RAG/LLM, generate architecture/system design questions.
- Include exactly 1 follow-up question per question.
- Do not provide answers.
"""
    response = _complete_mistral_chat(
        system_prompt="You generate structured interview preparation questions.",
        user_prompt=prompt,
        temperature=0.2,
    )
    payload = json.loads(response.choices[0].message.content)
    questions = [
        InterviewQuestion(**question)
        for question in payload.get("questions", [])
        if isinstance(question, dict)
    ]

    if not questions:
        raise ValueError("Mistral did not return preparation questions.")

    return PreparationInterviewResponse(
        role=role,
        selected_skills=selected_skills,
        questions=questions[:question_count],
    )


def _complete_mistral_chat(system_prompt: str, user_prompt: str, temperature: float):
    last_error: Exception | None = None
    for _ in range(2):
        try:
            return get_mistral_client().chat.complete(
                model=MISTRAL_API_MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                response_format={"type": "json_object"},
            )
        except Exception as exc:
            last_error = exc
            time.sleep(1)

    raise RuntimeError("Mistral request failed") from last_error
