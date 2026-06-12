from __future__ import annotations

import json
import re
import time
from pathlib import Path
from string import Template

from pydantic import ValidationError
import yaml

from backend.interview.expected_point_templates import python_expected_point_template
from backend.interview.grounding_index import ensure_grounding_index, retrieve_grounding_context
from backend.interview.python_test_case_templates import (
    python_test_cases_for_question,
    validate_python_test_cases,
)
from backend.interview.schemas import (
    GroundingIndexMode,
    InterviewQuestion,
    PreparationInterviewResponse,
    PreparationInterviewType,
    PreparationLevel,
    QuestionGenerationStrategy,
)
from backend.job_description.job_description_cleaner_mistral_api import (
    MISTRAL_API_MODEL_NAME,
    get_mistral_client,
)
from backend.matching.skill_matching_engine import skills_match


LEVEL_DIFFICULTY = {
    "beginner": "easy",
    "intermediate": "medium",
    "advanced": "hard",
}
TYPE_RULES = {
    "technical_theory": ("technical", False),
    "coding": ("coding", True),
    "project": ("project", False),
    "behavioral": ("behavioral", False),
}
EXTERNAL_TECH_REFERENCES = {
    "python",
    "pandas",
    "numpy",
    "polars",
    "dask",
    "pyspark",
    "sql",
    "java",
    "javascript",
    "typescript",
    "fastapi",
    "django",
    "flask",
    "react",
    "angular",
    "docker",
    "kubernetes",
    "langchain",
    "tensorflow",
    "pytorch",
    "rag",
}
PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "interview_preparation_question_generator.yml"
MAX_GENERATION_ATTEMPTS = 5


def generate_preparation_interview(
    role: str,
    selected_skills: list[str],
    candidate_projects: list[dict] | None = None,
    question_count: int = 5,
    level: PreparationLevel = "intermediate",
    interview_type: PreparationInterviewType = "mixed",
    generation_strategy: QuestionGenerationStrategy = "llm",
    grounding_query: str | None = None,
    grounding_index_mode: GroundingIndexMode = "use_existing",
    use_company_context: bool = False,
    company_context: dict[str, str] | None = None,
) -> PreparationInterviewResponse:
    selected_skills = _unique_non_empty(selected_skills)
    if not selected_skills:
        raise ValueError("Select at least one skill for preparation mode.")

    grounding_context: list[dict] = []
    if generation_strategy == "grounded":
        ensure_grounding_index(grounding_index_mode)
        query = grounding_query or " ".join([role, *selected_skills])
        grounding_context = retrieve_grounding_context(query)
        if not grounding_context:
            raise ValueError("No grounding context found for the selected skills.")
    grounding_used = _grounding_used(grounding_context)

    question_count = max(1, min(question_count, 20))
    accepted: list[InterviewQuestion] = []

    for _ in range(MAX_GENERATION_ATTEMPTS):
        remaining = question_count - len(accepted)
        if remaining <= 0:
            break
        response = _complete_mistral_chat(
            system_prompt=_prompt("preparation_question_system"),
            user_prompt=_build_prompt(
                role=role,
                selected_skills=selected_skills,
                question_count=remaining,
                level=level,
                interview_type=interview_type,
                candidate_projects=candidate_projects or [],
                existing_questions=[question.question for question in accepted],
                generation_strategy=generation_strategy,
                grounding_context=grounding_context,
                use_company_context=use_company_context,
                company_context=company_context,
            ),
            temperature=0.2,
        )
        payload = json.loads(response.choices[0].message.content)
        for raw_question in payload.get("questions", []):
            question = _validated_question(
                raw_question,
                selected_skills=selected_skills,
                level=level,
                interview_type=interview_type,
                generation_strategy=generation_strategy,
                grounding_used=grounding_used,
            )
            if not question:
                continue
            if any(_questions_are_similar(question.question, item.question) for item in accepted):
                continue
            accepted.append(question.model_copy(update={"id": f"q{len(accepted) + 1}"}))
            if len(accepted) == question_count:
                break

    if len(accepted) < question_count:
        raise ValueError(
            f"Mistral returned only {len(accepted)} valid questions out of {question_count}. "
            "Try fewer questions or a different interview type."
        )

    return PreparationInterviewResponse(
        role=role,
        selected_skills=selected_skills,
        level=level,
        interview_type=interview_type,
        questions=accepted,
    )


def regenerate_preparation_question(
    role: str,
    selected_skills: list[str],
    candidate_projects: list[dict],
    level: PreparationLevel,
    interview_type: PreparationInterviewType,
    question_id: str,
    existing_questions: list[InterviewQuestion],
    use_company_context: bool = False,
    company_context: dict[str, str] | None = None,
) -> InterviewQuestion:
    forbidden = [question.question for question in existing_questions]
    for _ in range(3):
        response = _complete_mistral_chat(
            system_prompt=_prompt("replacement_question_system"),
            user_prompt=_build_prompt(
                role=role,
                selected_skills=_unique_non_empty(selected_skills),
                question_count=1,
                level=level,
                interview_type=interview_type,
                candidate_projects=candidate_projects,
                existing_questions=forbidden,
                use_company_context=use_company_context,
                company_context=company_context,
            ),
            temperature=0.3,
        )
        payload = json.loads(response.choices[0].message.content)
        for raw_question in payload.get("questions", []):
            question = _validated_question(raw_question, selected_skills, level, interview_type)
            if question and not any(
                _questions_are_similar(question.question, existing.question)
                for existing in existing_questions
            ):
                return question.model_copy(update={"id": question_id})
    raise ValueError("Mistral could not generate a distinct replacement question.")


def _build_prompt(
    role: str,
    selected_skills: list[str],
    question_count: int,
    level: PreparationLevel,
    interview_type: PreparationInterviewType,
    candidate_projects: list[dict],
    existing_questions: list[str],
    generation_strategy: QuestionGenerationStrategy = "llm",
    grounding_context: list[dict] | None = None,
    use_company_context: bool = False,
    company_context: dict[str, str] | None = None,
) -> str:
    target_difficulty = LEVEL_DIFFICULTY[level]
    type_instruction = {
        "technical_theory": 'Every question_type must be "technical" and is_coding must be false.',
        "coding": 'Every question_type must be "coding" and is_coding must be true.',
        "project": 'Every question_type must be "project" and is_coding must be false.',
        "behavioral": 'Every question_type must be "behavioral" and is_coding must be false.',
        "mixed": 'Use a useful mix of "technical", "coding", "project", and "behavioral". Set is_coding true only for coding questions.',
    }[interview_type]
    grounded_prompt = ""
    if generation_strategy == "grounded":
        grounded_prompt = f"""
Generation strategy: grounded
Grounding context:
{json.dumps(grounding_context or [], ensure_ascii=False)}

Grounded generation rules:
- Generate every question only from the selected skills and grounding context.
- Do not introduce claims, APIs, policies, or architecture details absent from grounding context.
- Expected points, rubric, follow-up, and hint must also be supported by grounding context.
"""
    company_prompt = ""
    if use_company_context and company_context:
        company_prompt = f"""
Use company context: true
Company context:
{json.dumps(company_context, ensure_ascii=False)}

Company-context rules:
- Adapt questions to the company domain where appropriate.
- For coding questions, create realistic tasks related to the company context when natural.
- Do not force company context when it makes the question unnatural.
- Keep the assigned selected skill as the actual subject being assessed.
"""
    return Template(_prompt("preparation_question_user")).substitute(
        question_count=question_count,
        target_difficulty=target_difficulty,
        role=role,
        level=level,
        interview_type=interview_type,
        selected_skills=json.dumps(selected_skills, ensure_ascii=False),
        candidate_projects=json.dumps(candidate_projects, ensure_ascii=False),
        existing_questions=json.dumps(existing_questions, ensure_ascii=False),
        type_instruction=type_instruction,
        company_prompt=company_prompt,
        grounded_prompt=grounded_prompt,
    )

def _validated_question(
    raw_question: object,
    selected_skills: list[str],
    level: PreparationLevel,
    interview_type: PreparationInterviewType,
    generation_strategy: QuestionGenerationStrategy = "llm",
    grounding_used: list[str] | None = None,
) -> InterviewQuestion | None:
    if not isinstance(raw_question, dict):
        return None
    try:
        question = InterviewQuestion(**raw_question)
    except ValidationError:
        return None

    selected_by_normalized = {_normalize(skill): skill for skill in selected_skills}
    canonical_skill = selected_by_normalized.get(_normalize(question.skill or ""))
    if not canonical_skill:
        return None
    if question.difficulty != LEVEL_DIFFICULTY[level]:
        return None
    if len(question.expected_points) < 2 or len(question.scoring_rubric) < 2:
        return None
    if len(question.follow_up_questions) != 1:
        return None
    if not question.hint.strip():
        return None
    if _normalize(canonical_skill) not in _normalize(question.question):
        return None
    if not _criteria_stay_on_topic(question, canonical_skill):
        return None

    if interview_type != "mixed":
        expected_type, expected_coding = TYPE_RULES[interview_type]
        if question.question_type != expected_type or question.is_coding != expected_coding:
            return None
    else:
        if question.question_type not in {"technical", "coding", "project", "behavioral"}:
            return None
        if question.is_coding != (question.question_type == "coding"):
            return None

    trusted_template = python_expected_point_template(canonical_skill, question.question)
    updates = {
        "skill": canonical_skill,
        "source_group": "selected_skills",
        "generation_strategy": generation_strategy,
        "grounding_used": grounding_used or [],
    }
    if trusted_template:
        updates.update(
            {
                "criteria_source": "template",
                "expected_points": trusted_template["expected_points"],
                "scoring_rubric": trusted_template["scoring_rubric"],
            }
        )
    final_expected_points = updates.get("expected_points", question.expected_points)
    updates["expected_point_weights"] = _equal_weights(len(final_expected_points))
    if question.is_coding and _normalize(canonical_skill) == "python":
        updates["test_cases"] = (
            python_test_cases_for_question(canonical_skill, question.question)
            or validate_python_test_cases(question.test_cases)
        )
    return question.model_copy(update=updates)


def _criteria_stay_on_topic(question: InterviewQuestion, canonical_skill: str) -> bool:
    """Reject criteria that introduce recognized technologies absent from the question."""
    criteria_text = " ".join([*question.expected_points, *question.scoring_rubric])
    detected_skills = _external_technology_references(criteria_text)
    question_text = _normalize(question.question)
    for detected_skill in detected_skills:
        if skills_match(detected_skill, canonical_skill):
            continue
        if _normalize(detected_skill) in question_text:
            continue
        return False
    return True


def _external_technology_references(value: str) -> list[str]:
    normalized = _normalize(value)
    return [
        reference
        for reference in EXTERNAL_TECH_REFERENCES
        if re.search(rf"(?<![a-z0-9]){re.escape(_normalize(reference))}(?![a-z0-9])", normalized)
    ]


def _unique_non_empty(values: list[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        stripped = value.strip()
        normalized = _normalize(stripped)
        if stripped and normalized not in seen:
            seen.add(normalized)
            unique.append(stripped)
    return unique


def _equal_weights(count: int, total: float = 10.0) -> list[float]:
    if count <= 0:
        return []
    base = round(total / count, 2)
    weights = [base] * count
    weights[-1] = round(total - sum(weights[:-1]), 2)
    return weights


def _questions_are_similar(first: str, second: str, threshold: float = 0.72) -> bool:
    first_tokens = set(_normalize(first).split())
    second_tokens = set(_normalize(second).split())
    if not first_tokens or not second_tokens:
        return False
    overlap = len(first_tokens & second_tokens)
    jaccard_similarity = overlap / len(first_tokens | second_tokens)
    containment_similarity = overlap / min(len(first_tokens), len(second_tokens))
    return jaccard_similarity >= threshold or containment_similarity >= 0.8


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _grounding_used(grounding_context: list[dict]) -> list[str]:
    return list(dict.fromkeys(str(item.get("source", "unknown source")).strip() for item in grounding_context))


def _prompt(name: str) -> str:
    prompts = yaml.safe_load(PROMPT_PATH.read_text(encoding="utf-8")) or {}
    if name not in prompts:
        raise KeyError(f"Prompt '{name}' not found in {PROMPT_PATH}")
    return str(prompts[name])


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
