from __future__ import annotations

from collections import defaultdict


def build_progress_dashboard(sessions: list[dict]) -> dict:
    skill_scores: dict[str, list[float]] = defaultdict(list)
    type_scores: dict[str, list[float]] = defaultdict(list)
    score_trend = []
    retry_questions = []
    total_answers = 0

    for session in reversed(sessions):
        payload = session.get("payload", {})
        plan = payload.get("plan_response", {}).get("interview_plan", {})
        questions = {question.get("id"): question for question in plan.get("questions", [])}
        evaluations = payload.get("evaluations", {})
        session_scores = []
        for question_id, evaluation in evaluations.items():
            question = questions.get(question_id, {})
            score = float(evaluation.get("score", 0))
            skill = question.get("skill") or "General"
            question_type = question.get("question_type") or "technical"
            skill_scores[skill].append(score)
            type_scores[question_type].append(score)
            session_scores.append(score)
            total_answers += 1
            if score < 7:
                retry_questions.append(
                    {
                        "session_id": session["id"],
                        "question_id": question_id,
                        "question": question.get("question", ""),
                        "skill": skill,
                        "score": score,
                    }
                )
        if session_scores:
            score_trend.append(
                {
                    "date": session.get("updated_at", session.get("created_at")),
                    "role": plan.get("role", session.get("title")),
                    "average_score": _average(session_scores),
                }
            )

    average_by_skill = [
        {"skill": skill, "average_score": _average(scores), "attempts": len(scores)}
        for skill, scores in skill_scores.items()
    ]
    average_by_skill.sort(key=lambda item: item["average_score"], reverse=True)
    average_by_type = [
        {"type": question_type, "average_score": _average(scores), "attempts": len(scores)}
        for question_type, scores in type_scores.items()
    ]
    average_by_type.sort(key=lambda item: item["type"])

    weakest = list(reversed(average_by_skill[-3:]))
    next_topics = [item["skill"] for item in weakest] or ["Complete your first practice session"]
    return {
        "sessions": len(sessions),
        "answered_questions": total_answers,
        "overall_average": _average(
            [score for scores in skill_scores.values() for score in scores]
        ),
        "average_by_skill": average_by_skill,
        "average_by_type": average_by_type,
        "score_trend": score_trend,
        "strongest_topics": average_by_skill[:3],
        "weakest_topics": weakest,
        "retry_questions": retry_questions[:10],
        "recommended_next_session": {
            "skills": next_topics,
            "reason": "Focus on the lowest-scoring topics and retry missed questions.",
        },
    }


def _average(values: list[float]) -> float:
    if not values:
        return 0
    return round(sum(values) / len(values), 1)
