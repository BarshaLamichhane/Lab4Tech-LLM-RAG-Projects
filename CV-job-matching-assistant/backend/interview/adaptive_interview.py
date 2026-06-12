from __future__ import annotations

import json
import time
from pathlib import Path
from string import Template

import yaml
from pydantic import ValidationError

from backend.interview.expected_point_templates import python_expected_point_template
from backend.interview.grounding_index import ensure_grounding_index, retrieve_grounding_context
from backend.interview.interview_assistant import evaluate_answer
from backend.interview.python_test_case_templates import python_test_cases_for_question
from backend.interview.schemas import (
    AdaptiveInterviewAnswerRequest,
    AdaptiveInterviewResponse,
    AdaptiveInterviewStartRequest,
    AdaptiveInterviewState,
    AdaptiveInterviewTurn,
    InterviewQuestion,
)
from backend.job_description.job_description_cleaner_mistral_api import (
    MISTRAL_API_MODEL_NAME,
    get_mistral_client,
)


PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "adaptive_interview.yml"
DIFFICULTY_BY_LEVEL = {"beginner": "easy", "intermediate": "medium", "advanced": "hard"}
GROUNDED_SKILLS = {
    "langgraph", "langchain", "azure ai foundry", "openai api", "mistral api",
    "crewai", "mcp", "internal architecture", "company policy", "uploaded learning material",
}


def start_adaptive_interview(request: AdaptiveInterviewStartRequest) -> AdaptiveInterviewResponse:
    selected_skills = list(dict.fromkeys(skill.strip() for skill in request.selected_skills if skill.strip()))
    if len(selected_skills) != 1:
        raise ValueError("Adaptive interview currently requires exactly one selected skill.")

    grounding_context = _grounding_context(request, selected_skills[0])
    state = AdaptiveInterviewState(
        role=request.role,
        selected_skills=selected_skills,
        level=request.level,
        max_turns=request.max_turns,
        context=request.context,
        generation_strategy=request.generation_strategy,
        use_company_context=request.use_company_context,
        company_context=request.company_context,
        grounding_query=request.grounding_query,
        grounding_index_mode=request.grounding_index_mode,
    )
    question = _generate_next_question(state, grounding_context)
    state.turns.append(AdaptiveInterviewTurn(question=question))
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

    grounding_context = _grounding_context_from_state(state)
    next_question = _generate_next_question(state, grounding_context)
    state.turns.append(AdaptiveInterviewTurn(question=next_question))
    return AdaptiveInterviewResponse(state=state, next_question=next_question, finished=False)


def _generate_next_question(state: AdaptiveInterviewState, grounding_context: list[dict]) -> InterviewQuestion:
    skill = state.selected_skills[0]
    difficulty = _next_difficulty(state)
    question_id = f"adaptive-{len(state.turns) + 1}"
    prompt = Template(_prompt("adaptive_question_user")).substitute(
        question_id=question_id,
        role=state.role,
        skill=skill,
        difficulty=difficulty,
        history=json.dumps([turn.model_dump(mode="json") for turn in state.turns], ensure_ascii=False),
        company_prompt=_company_prompt(state),
        grounded_prompt=_grounded_prompt(state, grounding_context),
    )
    for _ in range(3):
        response = _complete_mistral_chat(_prompt("adaptive_question_system"), prompt, 0.2)
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
    raise ValueError("Mistral could not generate a valid adaptive interview question.")


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
    context = retrieve_grounding_context(state.grounding_query or f"{state.role} {state.selected_skills[0]}")
    if not context:
        raise ValueError(f"No grounding context found for {state.selected_skills[0]}.")
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
        skill=state.selected_skills[0],
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
        "recommended_next_steps": recommendations or [f"Continue focused practice on {state.selected_skills[0]}."],
    }


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
