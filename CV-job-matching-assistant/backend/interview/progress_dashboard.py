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


def build_adaptive_progress_dashboard(sessions: list[dict]) -> dict:
    skill_scores: dict[str, list[float]] = defaultdict(list)
    status_counts: dict[str, int] = defaultdict(int)
    readiness_trend = []
    recent_reports = []
    total_answers = 0

    for session in reversed(sessions):
        payload = session.get("payload", {})
        state = payload.get("state", {})
        learner_profile = state.get("learner_profile") or {}
        turns = state.get("turns", [])
        session_scores = []

        for turn in turns:
            evaluation = turn.get("evaluation")
            question = turn.get("question") or {}
            if not evaluation:
                continue
            score = float(evaluation.get("score", 0))
            skill = question.get("skill") or turn.get("selected_skill") or "General"
            skill_scores[skill].append(score)
            session_scores.append(score)
            total_answers += 1

        for skill_profile in learner_profile.get("skills", []):
            status = skill_profile.get("status")
            if status:
                status_counts[status] += 1

        readiness = float(learner_profile.get("readiness_score") or 0)
        if session_scores or readiness:
            readiness_trend.append(
                {
                    "date": session.get("updated_at", session.get("created_at")),
                    "role": state.get("role", session.get("title")),
                    "readiness_score": round(readiness, 1),
                    "average_score": _average(session_scores),
                }
            )

        recent_reports.append(
            {
                "session_id": session["id"],
                "title": session.get("title", "Adaptive interview"),
                "date": session.get("updated_at", session.get("created_at")),
                "role": state.get("role", ""),
                "average_score": _average(session_scores),
                "readiness_score": round(readiness, 1),
                "summary": _summary_text((payload.get("final_summary") or {}).get("summary")),
            }
        )

    average_by_skill = [
        {"skill": skill, "average_score": _average(scores), "attempts": len(scores)}
        for skill, scores in skill_scores.items()
    ]
    average_by_skill.sort(key=lambda item: item["average_score"], reverse=True)
    weakest = list(reversed(average_by_skill[-5:]))
    strongest = average_by_skill[:5]
    latest_profile = _latest_learner_profile(sessions)
    latest_weakest = latest_profile.get("weakest_skills") or [item["skill"] for item in weakest]
    latest_strongest = latest_profile.get("strongest_skills") or [item["skill"] for item in strongest]

    return {
        "sessions": len(sessions),
        "answered_questions": total_answers,
        "overall_average": _average(
            [score for scores in skill_scores.values() for score in scores]
        ),
        "latest_readiness_score": round(float(latest_profile.get("readiness_score") or 0), 1),
        "average_by_skill": average_by_skill,
        "strongest_skills": latest_strongest[:5],
        "weakest_skills": latest_weakest[:5],
        "skill_status_counts": {
            "weak": status_counts.get("weak", 0),
            "developing": status_counts.get("developing", 0),
            "strong": status_counts.get("strong", 0),
        },
        "readiness_trend": readiness_trend,
        "recent_reports": recent_reports[:10],
        "recommended_next_session": {
            "skills": latest_weakest[:3] or [item["skill"] for item in weakest[:3]],
            "reason": "Start the next adaptive session from the weakest high-priority skills.",
        },
    }


def _average(values: list[float]) -> float:
    if not values:
        return 0
    return round(sum(values) / len(values), 1)


def _latest_learner_profile(sessions: list[dict]) -> dict:
    for session in sessions:
        profile = (
            session.get("payload", {})
            .get("state", {})
            .get("learner_profile")
        )
        if isinstance(profile, dict):
            return profile
    return {}


def _summary_text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " | ".join(f"{key}: {_summary_text(item)}" for key, item in value.items())
    if isinstance(value, list):
        return ", ".join(_summary_text(item) for item in value)
    return "" if value is None else str(value)
