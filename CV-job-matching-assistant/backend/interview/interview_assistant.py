from __future__ import annotations

import json
import time

from backend.job_description.job_description_cleaner_mistral_api import (
    MISTRAL_API_MODEL_NAME,
    get_mistral_client,
)
from backend.interview.schemas import (
    AnswerEvaluation,
    InterviewContext,
    InterviewQuestion,
)
from backend.cv.cv_skill_extractor import extract_candidate_skill_profile
from backend.matching.skill_matching_engine import (
    DEFAULT_JOB_SKILLS_DIR,
    calculate_skill_match,
    get_saved_job_profile_by_role,
    skills_match,
)


def build_interview_context(
    cv_text: str,
    job_description_text: str | None = None,
    target_role: str | None = None,
) -> InterviewContext:
    if not cv_text.strip():
        raise ValueError("cv_text cannot be empty")

    if not target_role:
        raise ValueError("For now, please provide target_role.")

    job_profile = get_saved_job_profile_by_role(target_role, DEFAULT_JOB_SKILLS_DIR)
    candidate_profile = extract_candidate_skill_profile(cv_text, job_profiles=[job_profile])
    match_result = calculate_skill_match(candidate_profile, job_profile)

    required_skills = job_profile.get("required_skills", [])
    tools = job_profile.get("tools_and_platforms", [])

    matched_required = _skills_in_group(required_skills, match_result.matched_skills)
    matched_tools = _skills_in_group(tools, match_result.matched_skills)

    skill_groups = {
        "matched_strongly_required": match_result.matched_strongly_required_skills,
        "missing_strongly_required": match_result.missing_strongly_required_skills,
        "matched_skills": match_result.matched_skills,
        "missing_skills": match_result.missing_skills,
        "matched_required": matched_required,
        "missing_required": _exclude_skills(
            _skills_in_group(required_skills, match_result.missing_skills),
            matched_required,
        ),
        "matched_tools": matched_tools,
        "missing_tools": _exclude_skills(
            _skills_in_group(tools, match_result.missing_skills),
            matched_tools,
        ),
        "soft_skills": job_profile.get("soft_skills", []),
        "responsibilities": job_profile.get("responsibilities", []),
    }

    return InterviewContext(
        candidate_profile=candidate_profile.model_dump(),
        job_profile=job_profile,
        match_result=match_result.model_dump(),
        focus_skills=match_result.matched_skills,
        gap_skills=match_result.missing_skills,
        skill_groups=skill_groups,
    )


def evaluate_answer(
    question: InterviewQuestion,
    answer: str,
    context: InterviewContext | None = None,
    interview_engine: str = "mistral",
) -> AnswerEvaluation:
    if not answer.strip():
        return AnswerEvaluation(
            score=0,
            rating="Weak",
            strengths=[],
            weaknesses=["No answer provided"],
            missing_points=question.expected_points,
            feedback="Please provide an answer before evaluation.",
            improved_answer_outline=question.expected_points,
            follow_up_question=None,
            learning_recommendations=[question.skill] if question.skill else [],
        )

    prompt = f"""
You are a senior technical interviewer.

Evaluate the candidate answer.

Return ONLY valid JSON with this shape:
{{
  "score": 0-10,
  "rating": "Strong|Good|Needs improvement|Weak",
  "strengths": ["..."],
  "weaknesses": ["..."],
  "missing_points": ["..."],
  "feedback": "...",
  "improved_answer_outline": ["..."],
  "follow_up_question": "...",
  "learning_recommendations": ["..."]
}}

Question:
{question.model_dump_json()}

Candidate answer:
{answer}

Rules:
- Be strict but helpful.
- For coding answers, evaluate the submitted code together with stdout, stderr, exit code, timeout status, correctness, syntax, edge cases, readability, and complexity.
- Penalize syntax errors, runtime errors, timeouts, and wrong output even if the explanation sounds good.
- For SQL answers, evaluate joins, filtering, aggregation, correctness, and readability.
- For conceptual answers, evaluate accuracy, examples, trade-offs, and role relevance.
"""

    response = _complete_mistral_chat(
        system_prompt="You evaluate interview answers and return JSON.",
        user_prompt=prompt,
        temperature=0.0,
    )

    payload = json.loads(response.choices[0].message.content)
    return AnswerEvaluation(**payload)


def build_learning_path(
    context: InterviewContext,
    evaluations: list[AnswerEvaluation] | None = None,
) -> list[dict]:
    evaluations = evaluations or []

    weak_topics = []
    for evaluation in evaluations:
        if evaluation.score < 7:
            weak_topics.extend(evaluation.learning_recommendations)

    topics = weak_topics or context.gap_skills[:5]

    return [
        {
            "topic": topic,
            "priority": "High",
            "practice_tasks": [
                f"Review core concepts of {topic}",
                f"Answer 3 interview questions on {topic}",
                f"Prepare one project example using {topic}",
            ],
        }
        for topic in topics
    ]


def _skills_in_group(group_skills: list[str], compared_skills: list[str]) -> list[str]:
    return [
        skill
        for skill in group_skills
        if any(skills_match(skill, compared_skill) for compared_skill in compared_skills)
    ]


def _exclude_skills(values: list[str], excluded_values: list[str]) -> list[str]:
    return [
        value
        for value in values
        if not any(skills_match(value, excluded_value) for excluded_value in excluded_values)
    ]


def _complete_mistral_chat(system_prompt: str, user_prompt: str, temperature: float):
    last_error = None

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
