from __future__ import annotations

import json
import time

from backend.interview.schemas import (
    AdaptiveInterviewAnswerRequest,
    AdaptiveInterviewResponse,
    AdaptiveInterviewStartRequest,
    AdaptiveInterviewState,
    AdaptiveInterviewTurn,
)
from backend.job_description.job_description_cleaner_mistral_api import (
    MISTRAL_API_MODEL_NAME,
    get_mistral_client,
)


MAX_ADAPTIVE_TURNS = 5


def start_adaptive_interview(
    request: AdaptiveInterviewStartRequest,
) -> AdaptiveInterviewResponse:
    if not request.selected_skills:
        raise ValueError("Select at least one skill for adaptive mode.")

    state = AdaptiveInterviewState(
        role=request.role,
        selected_skills=request.selected_skills,
        level=request.level,
        turns=[],
    )
    first_question = _generate_next_question(state)
    state.turns.append(AdaptiveInterviewTurn(question=first_question))

    return AdaptiveInterviewResponse(
        state=state,
        next_question=first_question,
        finished=False,
    )


def submit_adaptive_answer(
    request: AdaptiveInterviewAnswerRequest,
) -> AdaptiveInterviewResponse:
    state = request.state
    if not state.turns:
        raise ValueError("No active interview question found.")

    current_turn = state.turns[-1]
    current_turn.answer = request.answer
    evaluation = _evaluate_turn(
        state=state,
        question=current_turn.question,
        answer=request.answer,
    )
    current_turn.feedback = evaluation.get("feedback")
    current_turn.score = evaluation.get("score")

    if len(state.turns) >= MAX_ADAPTIVE_TURNS:
        return AdaptiveInterviewResponse(
            state=state,
            next_question=None,
            finished=True,
            final_summary=_generate_final_summary(state),
        )

    next_question = _generate_next_question(state)
    state.turns.append(AdaptiveInterviewTurn(question=next_question))

    return AdaptiveInterviewResponse(
        state=state,
        next_question=next_question,
        finished=False,
    )


def _generate_next_question(state: AdaptiveInterviewState) -> str:
    prompt = f"""
You are conducting an adaptive technical interview.

Return ONLY valid JSON:
{{
  "next_question": "..."
}}

Role: {state.role}
Level: {state.level}
Selected skills: {json.dumps(state.selected_skills, ensure_ascii=False)}
Interview history: {json.dumps([turn.model_dump() for turn in state.turns], ensure_ascii=False)}

Rules:
- Ask only one question.
- Adapt the next question based on previous answer quality.
- If previous score was low, ask a simpler or clarifying question.
- If previous score was high, ask a deeper follow-up question.
- Stay focused on selected skills only.
"""
    response = _complete_mistral_chat(
        system_prompt="You generate one adaptive interview question.",
        user_prompt=prompt,
        temperature=0.2,
    )
    payload = json.loads(response.choices[0].message.content)
    return payload["next_question"]


def _evaluate_turn(
    state: AdaptiveInterviewState,
    question: str,
    answer: str,
) -> dict:
    prompt = f"""
Evaluate this adaptive interview answer.

Return ONLY valid JSON:
{{
  "score": 0-10,
  "feedback": "...",
  "strengths": ["..."],
  "weaknesses": ["..."]
}}

Role: {state.role}
Selected skills: {json.dumps(state.selected_skills, ensure_ascii=False)}
Question: {question}
Answer: {answer}

Rules:
- Be strict but helpful.
- Evaluate technical correctness, clarity, examples, and role relevance.
"""
    response = _complete_mistral_chat(
        system_prompt="You evaluate adaptive interview answers.",
        user_prompt=prompt,
        temperature=0.0,
    )
    return json.loads(response.choices[0].message.content)


def _generate_final_summary(state: AdaptiveInterviewState) -> str:
    prompt = f"""
Create a final interview summary.

Return ONLY valid JSON:
{{
  "summary": "..."
}}

Interview state:
{json.dumps(state.model_dump(), ensure_ascii=False)}

Include:
- overall readiness
- strongest skills
- weakest skills
- recommended next practice topics
"""
    response = _complete_mistral_chat(
        system_prompt="You summarize adaptive interview performance.",
        user_prompt=prompt,
        temperature=0.1,
    )
    payload = json.loads(response.choices[0].message.content)
    return payload["summary"]


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
