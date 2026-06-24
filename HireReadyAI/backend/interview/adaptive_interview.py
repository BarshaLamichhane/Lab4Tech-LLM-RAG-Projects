from __future__ import annotations

import json
import time
from pathlib import Path
from string import Template
from types import SimpleNamespace

import yaml
from pydantic import ValidationError

from backend.interview.expected_point_templates import python_expected_point_template
from backend.interview.grounding_index import ensure_grounding_index, retrieve_grounding_context
from backend.interview.interview_assistant import evaluate_answer
from backend.interview.python_test_case_templates import python_test_cases_for_question
from backend.interview.schemas import (
    AdaptiveInterviewAnswerRequest,
    AdaptiveLearnerProfile,
    AdaptiveInterviewResponse,
    AdaptiveInterviewStartRequest,
    AdaptiveInterviewState,
    AdaptiveInterviewTurn,
    AdaptiveSkillProfile,
    InterviewQuestion,
)
PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "adaptive_interview.yml"
DIFFICULTY_BY_LEVEL = {"beginner": "easy", "intermediate": "medium", "advanced": "hard"}
GROUNDED_SKILLS = {
    "langgraph", "langchain", "azure ai foundry", "openai api", "mistral api",
    "crewai", "mcp", "internal architecture", "company policy", "uploaded learning material",
}
ADAPTIVE_GROUP_RULES = [
    ("missing_strongly_required", 100, "missing", "strongly required"),
    ("missing_required", 90, "missing", "required"),
    ("missing_skills", 80, "missing", "required or preferred"),
    ("missing_tools", 75, "missing", "tool or platform"),
    ("matched_strongly_required", 65, "matched", "strongly required"),
    ("matched_required", 55, "matched", "required"),
    ("matched_skills", 45, "matched", "matched skill"),
    ("matched_tools", 35, "matched", "tool or platform"),
    ("soft_skills", 25, "unknown", "soft skill"),
    ("responsibilities", 20, "unknown", "responsibility"),
]
STATUS_SCORE = {"weak": 3.5, "developing": 6.0, "strong": 8.0}


def start_adaptive_interview(request: AdaptiveInterviewStartRequest) -> AdaptiveInterviewResponse:
    learner_profile = _build_learner_profile(request)
    selected_skills = [skill.skill for skill in learner_profile.skills]
    if not selected_skills:
        raise ValueError("No adaptive interview skills were found from the CV and selected role.")

    skill, reason = _choose_start_skill_from_profile(learner_profile, request.start_focus)
    grounding_context = _grounding_context(request, skill)
    state = AdaptiveInterviewState(
        role=request.role,
        selected_skills=selected_skills,
        level=request.level,
        max_turns=request.max_turns,
        start_focus=request.start_focus,
        context=request.context,
        generation_strategy=request.generation_strategy,
        use_company_context=request.use_company_context,
        company_context=request.company_context,
        grounding_query=request.grounding_query,
        grounding_index_mode=request.grounding_index_mode,
        learner_profile=learner_profile.model_copy(update={"next_focus": skill}),
        current_skill=skill,
        current_decision_reason=reason,
    )
    question = _generate_next_question(state, grounding_context)
    state.turns.append(AdaptiveInterviewTurn(question=question, selected_skill=skill, decision_reason=reason))
    return AdaptiveInterviewResponse(state=state, next_question=question, finished=False)


def submit_adaptive_answer(request: AdaptiveInterviewAnswerRequest) -> AdaptiveInterviewResponse:
    state = request.state
    if not state.turns or state.turns[-1].answer is not None:
        raise ValueError("No active adaptive interview question found.")
    if not request.answer.strip():
        raise ValueError("Provide an answer before continuing.")

    current_turn = state.turns[-1]
    current_turn.answer = request.answer
    current_turn.evaluation = evaluate_answer(
        current_turn.question,
        request.answer,
        context=state.context,
    )
    _update_learner_profile(state, current_turn.question.skill or state.current_skill or "", current_turn.evaluation.score)

    if len(state.turns) >= state.max_turns:
        try:
            final_summary = _generate_final_summary(state)
        except Exception:
            final_summary = _fallback_final_summary(state)
        return AdaptiveInterviewResponse(
            state=state,
            finished=True,
            final_summary=final_summary,
        )

    skill, reason = _choose_next_skill(state)
    state.current_skill = skill
    state.current_decision_reason = reason
    if state.learner_profile:
        state.learner_profile.next_focus = skill
    grounding_context = _grounding_context_from_state(state)
    next_question = _generate_next_question(state, grounding_context)
    state.turns.append(AdaptiveInterviewTurn(question=next_question, selected_skill=skill, decision_reason=reason))
    return AdaptiveInterviewResponse(state=state, next_question=next_question, finished=False)


def _generate_next_question(state: AdaptiveInterviewState, grounding_context: list[dict]) -> InterviewQuestion:
    skill = state.current_skill or (state.selected_skills[0] if state.selected_skills else "")
    if not skill:
        raise ValueError("No adaptive skill is available for the next question.")
    difficulty = _next_difficulty(state)
    question_id = f"adaptive-{len(state.turns) + 1}"
    prompt = Template(_prompt("adaptive_question_user")).substitute(
        question_id=question_id,
        role=state.role,
        skill=skill,
        difficulty=difficulty,
        learner_profile=json.dumps(state.learner_profile.model_dump(mode="json") if state.learner_profile else {}, ensure_ascii=False),
        decision_reason=state.current_decision_reason,
        history=json.dumps([turn.model_dump(mode="json") for turn in state.turns], ensure_ascii=False),
        company_prompt=_company_prompt(state),
        grounded_prompt=_grounded_prompt(state, grounding_context),
    )
    for _ in range(3):
        try:
            response = _complete_mistral_chat(_prompt("adaptive_question_system"), prompt, 0.2)
        except RuntimeError:
            break
        try:
            question = InterviewQuestion(**json.loads(response.choices[0].message.content)["question"])
        except (KeyError, TypeError, json.JSONDecodeError, ValidationError):
            continue
        if question.skill != skill or question.difficulty != difficulty or skill.casefold() not in question.question.casefold():
            continue
        updates = {
            "id": question_id,
            "source_group": "adaptive",
            "requires_grounding": state.generation_strategy == "grounded" or skill.casefold() in GROUNDED_SKILLS,
            "grounding_query": state.grounding_query,
            "generation_strategy": state.generation_strategy,
            "grounding_used": list(dict.fromkeys(item.get("source", "unknown") for item in grounding_context)),
            "expected_point_weights": _equal_weights(len(question.expected_points)),
        }
        template = python_expected_point_template(skill, question.question)
        if template:
            updates.update(
                criteria_source="template",
                expected_points=template["expected_points"],
                scoring_rubric=template["scoring_rubric"],
                expected_point_weights=_equal_weights(len(template["expected_points"])),
            )
        if question.is_coding and skill.casefold() == "python":
            updates["test_cases"] = python_test_cases_for_question(skill, question.question)
        return question.model_copy(update=updates)
    return _fallback_adaptive_question(question_id, skill, difficulty, state)


def _fallback_adaptive_question(
    question_id: str,
    skill: str,
    difficulty: str,
    state: AdaptiveInterviewState,
) -> InterviewQuestion:
    company_note = ""
    if state.use_company_context and state.company_context:
        context = state.company_context.get("company_context") or state.company_context.get("industry_domain")
        if context:
            company_note = f" in the context of {context}"
    return InterviewQuestion(
        id=question_id,
        question=(
            f"Explain one practical {skill} concept{company_note}. "
            "Include when you would use it, one short example, and one common mistake to avoid."
        ),
        question_type="technical",
        difficulty=difficulty,
        skill=skill,
        source_group="adaptive",
        is_coding=False,
        criteria_source="template",
        expected_points=[
            f"Accurately explains a relevant {skill} concept.",
            "Gives a concrete usage example.",
            "Mentions a realistic mistake, limitation, or trade-off.",
        ],
        expected_point_weights=[4.0, 3.0, 3.0],
        follow_up_questions=[f"How would you apply this {skill} concept in a real project?"],
        scoring_rubric=[
            "Strong answers are accurate, specific, and connected to practical use.",
            "Weak answers stay vague or do not explain the concept clearly.",
        ],
        hint="Use one concrete example instead of only definitions.",
        requires_grounding=state.generation_strategy == "grounded" or skill.casefold() in GROUNDED_SKILLS,
        grounding_query=state.grounding_query,
        generation_strategy=state.generation_strategy,
    )


def _build_learner_profile(request: AdaptiveInterviewStartRequest) -> AdaptiveLearnerProfile:
    if not request.context:
        raise ValueError("Adaptive interview needs a CV-to-role comparison context.")
    allowed = {_normalize(skill) for skill in request.selected_skills if skill.strip()}
    skills: dict[str, AdaptiveSkillProfile] = {}
    for source_group, priority, cv_status, job_importance in ADAPTIVE_GROUP_RULES:
        for skill in request.context.skill_groups.get(source_group, []):
            normalized = _normalize(skill)
            if not normalized or (allowed and normalized not in allowed):
                continue
            existing = skills.get(normalized)
            if existing and existing.priority >= priority:
                continue
            estimated_score = _initial_estimated_score(cv_status, source_group)
            skills[normalized] = AdaptiveSkillProfile(
                skill=skill,
                source_group=source_group,
                priority=priority,
                cv_status=cv_status,
                job_importance=job_importance,
                estimated_score=estimated_score,
                status=_status_for_score(estimated_score),
            )
    ordered = sorted(skills.values(), key=lambda item: (-item.priority, item.skill.casefold()))
    readiness = _readiness_score(request.context.match_result)
    profile = AdaptiveLearnerProfile(
        goal_role=request.role,
        readiness_score=readiness,
        skills=ordered,
    )
    _refresh_profile_summary(profile)
    return profile


def _choose_next_skill(state: AdaptiveInterviewState) -> tuple[str, str]:
    if not state.learner_profile:
        profile = _build_learner_profile(
            AdaptiveInterviewStartRequest(
                role=state.role,
                selected_skills=state.selected_skills,
                level=state.level,
                max_turns=state.max_turns,
                start_focus=state.start_focus,
                context=state.context,
            )
        )
        state.learner_profile = profile
    last_turn = state.turns[-1] if state.turns else None
    last_score = last_turn.evaluation.score if last_turn and last_turn.evaluation else None
    last_skill = last_turn.question.skill if last_turn else state.current_skill
    if last_skill and last_score is not None:
        attempts = _skill_attempts(state, last_skill)
        if last_score < 5:
            return last_skill, f"{last_skill} stayed weak after scoring {last_score}/10, so the next question reinforces the same skill."
        if last_score < 8 and attempts < 2:
            return last_skill, f"{last_skill} is developing after scoring {last_score}/10, so one more question checks consistency."
    return _choose_next_skill_from_profile(state.learner_profile, state.level, exclude_strong=True)


def _choose_start_skill_from_profile(
    profile: AdaptiveLearnerProfile,
    start_focus: str,
) -> tuple[str, str]:
    if start_focus == "strong":
        candidates = [
            skill for skill in profile.skills
            if skill.cv_status == "matched" or skill.status == "strong"
        ] or profile.skills
        chosen = max(candidates, key=lambda item: (item.priority, item.estimated_score))
        return (
            chosen.skill,
            f"{chosen.skill} is the highest-priority strong or matched skill for {profile.goal_role}, so the session starts by validating a strength.",
        )
    return _choose_next_skill_from_profile(profile, "intermediate")


def _choose_next_skill_from_profile(
    profile: AdaptiveLearnerProfile,
    level: str,
    exclude_strong: bool = False,
) -> tuple[str, str]:
    candidates = [
        skill for skill in profile.skills
        if not (exclude_strong and skill.status == "strong" and skill.attempts > 0)
    ] or profile.skills
    if not candidates:
        raise ValueError("No adaptive interview skills are available.")
    chosen = max(candidates, key=_adaptive_priority)
    reason = (
        f"{chosen.skill} is the highest-priority {chosen.cv_status} {chosen.job_importance} "
        f"skill for {profile.goal_role}. Current status: {chosen.status}."
    )
    return chosen.skill, reason


def _adaptive_priority(skill: AdaptiveSkillProfile) -> float:
    score = skill.average_score if skill.average_score is not None else skill.estimated_score
    weakness_boost = max(0.0, 8.0 - score) * 8
    repeat_penalty = min(skill.attempts, 3) * 8
    return skill.priority + weakness_boost - repeat_penalty


def _update_learner_profile(state: AdaptiveInterviewState, skill_name: str, score: float) -> None:
    if not state.learner_profile or not skill_name:
        return
    normalized = _normalize(skill_name)
    for index, skill in enumerate(state.learner_profile.skills):
        if _normalize(skill.skill) != normalized:
            continue
        previous_total = (skill.average_score if skill.average_score is not None else 0) * skill.attempts
        attempts = skill.attempts + 1
        average = round((previous_total + score) / attempts, 1)
        state.learner_profile.skills[index] = skill.model_copy(
            update={
                "attempts": attempts,
                "average_score": average,
                "last_score": score,
                "status": _status_for_score(average),
            }
        )
        break
    _refresh_profile_summary(state.learner_profile)


def _refresh_profile_summary(profile: AdaptiveLearnerProfile) -> None:
    ordered_by_score = sorted(
        profile.skills,
        key=lambda item: item.average_score if item.average_score is not None else item.estimated_score,
    )
    profile.weakest_skills = [item.skill for item in ordered_by_score[:5]]
    profile.strongest_skills = [item.skill for item in reversed(ordered_by_score[-5:])]
    if any(item.attempts for item in profile.skills):
        weighted_total = sum(
            (item.average_score if item.average_score is not None else item.estimated_score) * item.priority
            for item in profile.skills
        )
        total_priority = sum(item.priority for item in profile.skills)
        if total_priority:
            profile.readiness_score = round((weighted_total / total_priority) * 10, 1)


def _skill_attempts(state: AdaptiveInterviewState, skill_name: str) -> int:
    normalized = _normalize(skill_name)
    return sum(1 for turn in state.turns if _normalize(turn.question.skill or "") == normalized and turn.evaluation)


def _initial_estimated_score(cv_status: str, source_group: str) -> float:
    if cv_status == "matched":
        return 7.5 if "strongly" not in source_group else 8.0
    if cv_status == "missing":
        return 3.5 if "strongly" in source_group else 4.0
    return 5.0


def _status_for_score(score: float) -> str:
    if score >= STATUS_SCORE["strong"]:
        return "strong"
    if score >= STATUS_SCORE["developing"]:
        return "developing"
    return "weak"


def _readiness_score(match_result: dict) -> float:
    try:
        return round(float(match_result.get("score", 0)), 1)
    except (TypeError, ValueError):
        return 0.0


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def _next_difficulty(state: AdaptiveInterviewState) -> str:
    if not state.turns or state.turns[-1].evaluation is None:
        return DIFFICULTY_BY_LEVEL.get(state.level, "medium")
    score = state.turns[-1].evaluation.score
    current = state.turns[-1].question.difficulty
    levels = ["easy", "medium", "hard"]
    index = levels.index(current)
    if score >= 8:
        return levels[min(index + 1, 2)]
    if score < 5:
        return levels[max(index - 1, 0)]
    return current


def _grounding_context(request: AdaptiveInterviewStartRequest, skill: str) -> list[dict]:
    if request.generation_strategy != "grounded":
        return []
    ensure_grounding_index(request.grounding_index_mode)
    context = retrieve_grounding_context(request.grounding_query or f"{request.role} {skill}")
    if not context:
        raise ValueError(f"No grounding context found for {skill}.")
    return context


def _grounding_context_from_state(state: AdaptiveInterviewState) -> list[dict]:
    if state.generation_strategy != "grounded":
        return []
    ensure_grounding_index(state.grounding_index_mode)
    skill = state.current_skill or (state.selected_skills[0] if state.selected_skills else "")
    context = retrieve_grounding_context(state.grounding_query or f"{state.role} {skill}")
    if not context:
        raise ValueError(f"No grounding context found for {skill}.")
    return context


def _company_prompt(state: AdaptiveInterviewState) -> str:
    if not state.use_company_context or not state.company_context:
        return ""
    return (
        f"Company context: {json.dumps(state.company_context, ensure_ascii=False)}\n"
        "Use the company domain naturally, but keep the selected skill as the subject."
    )


def _grounded_prompt(state: AdaptiveInterviewState, context: list[dict]) -> str:
    if state.generation_strategy != "grounded":
        return ""
    return (
        f"Verified grounding context: {json.dumps(context, ensure_ascii=False)}\n"
        "Generate the question only from the selected skill and verified context."
    )


def _generate_final_summary(state: AdaptiveInterviewState) -> dict:
    prompt = Template(_prompt("adaptive_summary_user")).substitute(
        role=state.role,
        learner_profile=json.dumps(state.learner_profile.model_dump(mode="json") if state.learner_profile else {}, ensure_ascii=False),
        turns=json.dumps([turn.model_dump(mode="json") for turn in state.turns], ensure_ascii=False),
    )
    response = _complete_mistral_chat(_prompt("adaptive_summary_system"), prompt, 0.1)
    return _normalized_final_summary(json.loads(response.choices[0].message.content))


def _fallback_final_summary(state: AdaptiveInterviewState) -> dict:
    evaluations = [
        turn.evaluation
        for turn in state.turns
        if turn.evaluation is not None
    ]
    average = round(sum(item.score for item in evaluations) / len(evaluations), 1) if evaluations else 0
    strengths = list(dict.fromkeys(point for item in evaluations for point in item.strengths))[:3]
    improvements = list(dict.fromkeys(point for item in evaluations for point in item.weaknesses))[:3]
    recommendations = list(
        dict.fromkeys(point for item in evaluations for point in item.learning_recommendations)
    )[:3]
    return {
        "summary": f"Completed {len(evaluations)} adaptive turns with an average score of {average}/10.",
        "strongest_points": strengths,
        "improvement_areas": improvements,
        "recommended_next_steps": recommendations or _fallback_recommendations(state),
    }


def _fallback_recommendations(state: AdaptiveInterviewState) -> list[str]:
    if not state.learner_profile:
        return ["Continue another adaptive session using the lowest-scoring interview topics."]
    weakest = state.learner_profile.weakest_skills[:3]
    if not weakest:
        return ["Continue another adaptive session to confirm role readiness."]
    return [
        f"Practise {skill} next because it remains one of the lowest-readiness skills."
        for skill in weakest
    ]


def _normalized_final_summary(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Adaptive final summary must be a JSON object.")
    summary = payload.get("summary", "")
    return {
        "summary": _summary_item_text(summary),
        "strongest_points": _summary_items(payload.get("strongest_points")),
        "improvement_areas": _summary_items(payload.get("improvement_areas")),
        "recommended_next_steps": _summary_items(payload.get("recommended_next_steps")),
    }


def _summary_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [
        text
        for item in value
        if (text := _summary_item_text(item))
    ]


def _summary_item_text(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return " | ".join(
            f"{str(key).replace('_', ' ').title()}: {_summary_item_text(item)}"
            for key, item in value.items()
            if _summary_item_text(item)
        )
    if isinstance(value, list):
        return ", ".join(text for item in value if (text := _summary_item_text(item)))
    if value is None:
        return ""
    return str(value)


def _equal_weights(count: int) -> list[float]:
    if count <= 0:
        return []
    weights = [round(10 / count, 2)] * count
    weights[-1] = round(10 - sum(weights[:-1]), 2)
    return weights


def _prompt(name: str) -> str:
    prompts = yaml.safe_load(PROMPT_PATH.read_text(encoding="utf-8")) or {}
    return str(prompts[name])


def _complete_mistral_chat(system_prompt: str, user_prompt: str, temperature: float):
    from backend.app.llm_client import complete_json_chat

    last_error: Exception | None = None
    for _ in range(2):
        try:
            response = complete_json_chat(system_prompt, user_prompt, temperature)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=response.content))]
            )
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError("Mistral request failed") from last_error
