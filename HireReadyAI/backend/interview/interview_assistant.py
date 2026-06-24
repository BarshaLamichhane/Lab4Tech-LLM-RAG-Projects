from __future__ import annotations

import ast
import json
import re
import time
from types import SimpleNamespace

from backend.app.config import CONFIG
from backend.interview.code_runner import run_python_code
from backend.interview.grounding_retriever import retrieve_grounding_context
from backend.interview.python_test_case_templates import validate_python_test_cases
from backend.interview.schemas import (
    AnswerEvaluation,
    CodeRunRequest,
    ExpectedPointAssessment,
    InterviewContext,
    InterviewQuestion,
    ScoreBreakdownItem,
)
from backend.cv.cv_skill_extractor import extract_candidate_skill_profile
from backend.matching.skill_matching_engine import (
    DEFAULT_JOB_SKILLS_DIR,
    calculate_skill_match,
    get_saved_job_profile_by_role,
    skills_match,
)

NON_CODING_SCORE_BUDGET = {
    "technical_correctness": ("Technical correctness", 4.0),
    "completeness": ("Completeness", 2.5),
    "communication": ("Communication", 1.5),
    "examples": ("Examples", 2.0),
    "code_quality": ("Code quality", 0.0),
}
CODING_SCORE_BUDGET = {
    "technical_correctness": ("Technical correctness", 3.0),
    "completeness": ("Completeness", 2.0),
    "communication": ("Communication", 1.0),
    "examples": ("Examples", 0.5),
    "code_quality": ("Code quality", 3.5),
}
GROUNDED_SKILLS = {
    "langgraph",
    "langchain",
    "azure ai foundry",
    "openai api",
    "mistral api",
    "crewai",
    "mcp",
    "internal architecture",
    "company policy",
    "uploaded learning material",
}


def select_evaluation_strategy(question: InterviewQuestion) -> str:
    skill = (question.skill or "").casefold().strip()
    if question.is_coding and skill in {"python", "sql"}:
        return "test_based"
    if question.requires_grounding or skill in GROUNDED_SKILLS:
        return "grounded"
    return "rubric"


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
    evaluation, _, _ = evaluate_answer_with_audit(
        question=question,
        answer=answer,
        context=context,
        interview_engine=interview_engine,
    )
    return evaluation


def evaluate_answer_with_audit(
    question: InterviewQuestion,
    answer: str,
    context: InterviewContext | None = None,
    interview_engine: str = "mistral",
) -> tuple[AnswerEvaluation, str, str]:
    strategy = select_evaluation_strategy(question)
    execution_result = None
    grounding_context: list[str] = []
    grounding_used: list[str] = []
    score_cap = 10.0

    if strategy == "test_based":
        if (question.skill or "").casefold().strip() == "python":
            execution_result, score_cap = _run_python_test_evaluation(question, answer)
        else:
            execution_result = {
                "language": "sql",
                "runner_available": False,
                "message": "No safe SQL runner is configured. SQL was evaluated with the rubric.",
                "test_cases": question.test_cases,
            }
    elif strategy == "grounded":
        grounding_context, grounding_used = retrieve_grounding_context(question, context)

    point_weights = _expected_point_weights(question)
    score_budget = CODING_SCORE_BUDGET if question.is_coding else NON_CODING_SCORE_BUDGET
    if not answer.strip():
        evaluation = AnswerEvaluation(
            score=0,
            rating="Weak",
            strengths=[],
            weaknesses=["No answer provided"],
            missing_points=question.expected_points,
            feedback="Please provide an answer before evaluation.",
            improved_answer_outline=question.expected_points,
            follow_up_question=None,
            learning_recommendations=[question.skill] if question.skill else [],
            expected_point_assessments=[
                ExpectedPointAssessment(
                    point=point,
                    weight=weight,
                    awarded_score=0,
                    explanation="No answer was provided.",
                )
                for point, weight in zip(question.expected_points, point_weights)
            ],
            score_breakdown=[
                ScoreBreakdownItem(
                    category=category,
                    label=label,
                    max_score=max_score,
                    awarded_score=0,
                    explanation="No answer was provided.",
                )
                for category, (label, max_score) in score_budget.items()
            ],
            evaluation_strategy=strategy,
            execution_result=execution_result,
            grounding_used=grounding_used,
        )
        return evaluation, "", ""

    weighted_points = [
        {"point": point, "weight": weight}
        for point, weight in zip(question.expected_points, point_weights)
    ]
    category_budget = [
        {"category": category, "label": label, "max_score": max_score}
        for category, (label, max_score) in score_budget.items()
    ]
    strategy_context, strategy_rules = _strategy_prompt_context(
        strategy=strategy,
        execution_result=execution_result,
        grounding_context=grounding_context,
    )
    prompt = f"""
You are a senior technical interviewer.

Evaluate the candidate answer using the exact expected-point weights and category budgets below.
The application calculates the final score from category awarded scores. Do not invent another score.

Return ONLY valid JSON with this shape:
{{
  "rating": "Strong|Good|Needs improvement|Weak",
  "strengths": ["..."],
  "weaknesses": ["..."],
  "missing_points": ["..."],
  "feedback": "...",
  "improved_answer_outline": ["..."],
  "follow_up_question": "...",
  "learning_recommendations": ["..."],
  "expected_point_assessments": [
    {{
      "point": "exact expected point",
      "weight": 0.0,
      "awarded_score": 0.0,
      "explanation": "specific evidence from the answer or what was missing"
    }}
  ],
  "score_breakdown": [
    {{
      "category": "technical_correctness|completeness|communication|examples|code_quality",
      "label": "category display label",
      "max_score": 0.0,
      "awarded_score": 0.0,
      "explanation": "specific reason for this category score"
    }}
  ]
}}

Question:
{question.model_dump_json()}

Expected points and fixed weights:
{json.dumps(weighted_points, ensure_ascii=False)}

Fixed category score budget:
{json.dumps(category_budget, ensure_ascii=False)}

Candidate answer:
{answer}

Evaluation strategy: {strategy}
{strategy_context}

Rules:
- Return exactly one expected_point_assessment for every supplied expected point, in the same order.
- Copy each expected point and its weight exactly.
- Return exactly one score_breakdown item for every supplied category, in the same order.
- Copy category, label, and max_score exactly.
- awarded_score must be between 0 and its corresponding weight or max_score.
- Explain how the candidate answer affected every expected point and category score.
- Be strict but helpful.
- For coding answers, evaluate the submitted code together with stdout, stderr, exit code, timeout status, correctness, syntax, edge cases, readability, and complexity.
- Penalize syntax errors, runtime errors, timeouts, and wrong output even if the explanation sounds good.
- For SQL answers, evaluate joins, filtering, aggregation, correctness, and readability.
- For conceptual answers, evaluate accuracy, examples, trade-offs, and role relevance.
{strategy_rules}
"""

    validation_error: Exception | None = None
    attempt_prompt = prompt
    for _ in range(2):
        response = _complete_mistral_chat(
            system_prompt="You evaluate interview answers and return JSON.",
            user_prompt=attempt_prompt,
            temperature=0.0,
        )
        raw_response = response.choices[0].message.content
        try:
            payload = json.loads(raw_response)
            evaluation = _validated_evaluation(
                payload,
                question,
                point_weights,
                score_budget,
                evaluation_strategy=strategy,
                execution_result=execution_result,
                grounding_used=grounding_used,
                score_cap=score_cap,
            )
            if _substantive_answer(answer) and _looks_like_no_attempt_evaluation(evaluation):
                raise ValueError("Mistral treated a substantive answer as no attempt")
            return evaluation, attempt_prompt, raw_response
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            validation_error = exc
            attempt_prompt = (
                f"{prompt}\n\nYour previous response failed validation: {exc}. "
                "Return the complete required JSON structure and obey every fixed weight."
            )
    raise ValueError("Mistral returned an invalid structured evaluation") from validation_error


def _validated_evaluation(
    payload: dict,
    question: InterviewQuestion,
    point_weights: list[float],
    score_budget: dict[str, tuple[str, float]],
    evaluation_strategy: str = "rubric",
    execution_result: dict | None = None,
    grounding_used: list[str] | None = None,
    score_cap: float = 10.0,
) -> AnswerEvaluation:
    raw_point_assessments = payload.get("expected_point_assessments", [])
    if len(raw_point_assessments) != len(question.expected_points):
        raise ValueError("Mistral did not assess every expected point")

    point_assessments = []
    for expected_point, weight, assessment in zip(
        question.expected_points,
        point_weights,
        raw_point_assessments,
    ):
        awarded = _bounded_score(assessment.get("awarded_score"), weight)
        point_assessments.append(
            ExpectedPointAssessment(
                point=expected_point,
                weight=weight,
                awarded_score=awarded,
                explanation=str(assessment.get("explanation", "")).strip()
                or "No explanation supplied.",
            )
        )

    raw_breakdown_by_category = {
        item.get("category"): item
        for item in payload.get("score_breakdown", [])
        if isinstance(item, dict)
    }
    score_breakdown = []
    for category, (label, max_score) in score_budget.items():
        item = raw_breakdown_by_category.get(category)
        if not item:
            raise ValueError(f"Mistral did not score category: {label}")
        score_breakdown.append(
            ScoreBreakdownItem(
                category=category,
                label=label,
                max_score=max_score,
                awarded_score=_bounded_score(item.get("awarded_score"), max_score),
                explanation=str(item.get("explanation", "")).strip()
                or "No explanation supplied.",
            )
        )

    score = round(sum(item.awarded_score for item in score_breakdown), 1)
    if score > score_cap and score > 0:
        score_breakdown = _capped_score_breakdown(score_breakdown, score_cap)
        score = round(sum(item.awarded_score for item in score_breakdown), 1)
    normalized_payload = {
        **payload,
        "score": score,
        "rating": _rating_for_score(score),
        "expected_point_assessments": point_assessments,
        "score_breakdown": score_breakdown,
        "evaluation_strategy": evaluation_strategy,
        "execution_result": execution_result,
        "grounding_used": grounding_used or [],
    }
    return AnswerEvaluation(**normalized_payload)


def _substantive_answer(answer: str) -> bool:
    compact = re.sub(r"\s+", " ", answer).strip()
    words = re.findall(r"\b\w+\b", compact)
    return len(compact) >= 60 and len(words) >= 8


def _looks_like_no_attempt_evaluation(evaluation: AnswerEvaluation) -> bool:
    if evaluation.score > 0:
        return False
    text = " ".join(
        [
            evaluation.feedback,
            *evaluation.weaknesses,
            *[item.explanation for item in evaluation.score_breakdown],
            *[item.explanation for item in evaluation.expected_point_assessments],
        ]
    ).casefold()
    no_attempt_terms = [
        "no answer",
        "no attempt",
        "did not attempt",
        "answer was not provided",
        "candidate did not provide",
    ]
    return any(term in text for term in no_attempt_terms)


def _strategy_prompt_context(
    strategy: str,
    execution_result: dict | None,
    grounding_context: list[str],
) -> tuple[str, str]:
    if strategy == "test_based":
        return (
            f"Execution and test results:\n{json.dumps(execution_result, ensure_ascii=False)}",
            (
                "- Treat execution and test results as authoritative.\n"
                "- Do not reward claimed correctness that contradicts failed execution or tests.\n"
                "- For SQL without a safe runner, evaluate against the supplied schema, test cases, "
                "expected outputs, and rubric only."
            ),
        )
    if strategy == "grounded":
        return (
            f"Retrieved grounding context:\n{json.dumps(grounding_context, ensure_ascii=False)}",
            (
                "- Treat retrieved grounding context as the source of truth.\n"
                "- Do not reward claims that contradict the retrieved context.\n"
                "- Penalize unsupported claims and mention contradictions in weaknesses."
            ),
        )
    return "", "- Use the existing expected points and rubric as the evaluation source."


def _run_python_test_evaluation(
    question: InterviewQuestion,
    answer: str,
) -> tuple[dict, float]:
    if not CONFIG.code_execution_enabled:
        return {
            "language": "python",
            "runner_available": False,
            "message": "Python test execution is disabled. The answer was evaluated with the rubric.",
            "test_cases": question.test_cases,
        }, 10.0

    code = _extract_candidate_code(answer)
    if not code.strip():
        return {
            "language": "python",
            "runner_available": True,
            "passed": 0,
            "failed": len(question.test_cases),
            "tests": [],
            "error": "No Python code found in the candidate answer.",
        }, 4.0

    test_cases = validate_python_test_cases(question.test_cases)
    if not test_cases:
        test_cases = [{"input": "", "expected_output": None}]
    results = []
    passed = 0
    failed = 0
    execution_error = False
    for index, test_case in enumerate(test_cases, start=1):
        test_code = _code_with_function_test_harness(code, test_case)
        run_result = run_python_code(
            CodeRunRequest(code=test_code, stdin=str(test_case.get("input", "")))
        )
        expected_output = test_case.get("expected_output")
        actual_output = _comparable_output(run_result.stdout, test_case)
        comparable_expected = _comparable_expected_output(expected_output, test_case)
        output_matches = (
            run_result.exit_code == 0
            and not run_result.timed_out
            and (
                expected_output is None
                or actual_output == comparable_expected
            )
        )
        if output_matches:
            passed += 1
        else:
            failed += 1
        if run_result.exit_code not in {0, None} or run_result.timed_out:
            execution_error = True
        results.append(
            {
                "test": index,
                "input": test_case.get("input", ""),
                "args": test_case.get("args"),
                "expected_output": expected_output,
                "stdout": run_result.stdout,
                "stderr": run_result.stderr,
                "exit_code": run_result.exit_code,
                "timed_out": run_result.timed_out,
                "passed": output_matches,
            }
        )

    score_cap = 4.0 if execution_error else 6.0 if failed > passed else 10.0
    return {
        "language": "python",
        "runner_available": True,
        "passed": passed,
        "failed": failed,
        "tests": results,
    }, score_cap


def _code_with_function_test_harness(code: str, test_case: dict) -> str:
    if "args" not in test_case:
        return code
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code
    function = next(
        (
            node.name
            for node in reversed(tree.body)
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
        ),
        None,
    )
    if not function:
        return code
    args_json = json.dumps(test_case["args"])
    return (
        f"{code}\n\n"
        "import json as __hire_ready_json\n"
        f"__hire_ready_args = __hire_ready_json.loads({args_json!r})\n"
        f"__hire_ready_result = {function}(*__hire_ready_args)\n"
        "print(__hire_ready_json.dumps(__hire_ready_result, sort_keys=True))\n"
    )


def _comparable_output(stdout: str, test_case: dict) -> str:
    stripped = stdout.strip()
    if "args" not in test_case:
        return stripped
    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def _comparable_expected_output(expected_output: object, test_case: dict) -> str:
    if "args" in test_case:
        return json.dumps(expected_output, sort_keys=True)
    return str(expected_output).strip()


def _extract_candidate_code(answer: str) -> str:
    fenced_code = re.search(r"```(?:python)?\s*(.*?)```", answer, flags=re.IGNORECASE | re.DOTALL)
    return fenced_code.group(1).strip() if fenced_code else answer.strip()


def _capped_score_breakdown(
    score_breakdown: list[ScoreBreakdownItem],
    score_cap: float,
) -> list[ScoreBreakdownItem]:
    total = sum(item.awarded_score for item in score_breakdown)
    if total <= score_cap or total <= 0:
        return score_breakdown
    remaining = score_cap
    capped = []
    for index, item in enumerate(score_breakdown):
        if index == len(score_breakdown) - 1:
            awarded = round(max(0.0, remaining), 1)
        else:
            awarded = round(min(item.awarded_score * score_cap / total, remaining), 1)
            remaining = round(remaining - awarded, 1)
        capped.append(item.model_copy(update={"awarded_score": awarded}))
    return capped


def _expected_point_weights(question: InterviewQuestion) -> list[float]:
    if (
        len(question.expected_point_weights) == len(question.expected_points)
        and round(sum(question.expected_point_weights), 2) == 10.0
    ):
        return question.expected_point_weights
    count = len(question.expected_points)
    if count == 0:
        return []
    weight = round(10 / count, 2)
    weights = [weight] * count
    weights[-1] = round(10 - sum(weights[:-1]), 2)
    return weights


def _bounded_score(value: object, maximum: float) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = 0.0
    return round(max(0.0, min(score, maximum)), 1)


def _rating_for_score(score: float) -> str:
    if score >= 8.5:
        return "Strong"
    if score >= 7:
        return "Good"
    if score >= 4:
        return "Needs improvement"
    return "Weak"


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
    from backend.app.llm_client import complete_json_chat

    last_error = None

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
