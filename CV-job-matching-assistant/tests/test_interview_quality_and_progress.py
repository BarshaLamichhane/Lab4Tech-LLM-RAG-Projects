from unittest import TestCase

from backend.interview.preparation_interview import _questions_are_similar
from backend.interview.progress_dashboard import build_adaptive_progress_dashboard, build_progress_dashboard


class InterviewQuestionQualityTests(TestCase):
    def test_detects_nearly_identical_questions(self):
        self.assertTrue(
            _questions_are_similar(
                "Explain how Python generators improve memory efficiency.",
                "Explain how Python generators improve memory efficiency for large data.",
            )
        )

    def test_distinct_questions_are_allowed(self):
        self.assertFalse(
            _questions_are_similar(
                "Explain Python generators.",
                "Implement a Python context manager.",
            )
        )


class InterviewProgressDashboardTests(TestCase):
    def test_aggregates_skills_types_trends_and_retry_queue(self):
        sessions = [
            {
                "id": "session-1",
                "title": "AI Engineer practice",
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-01T00:00:00+00:00",
                "payload": {
                    "plan_response": {
                        "interview_plan": {
                            "role": "AI Engineer",
                            "questions": [
                                {
                                    "id": "q1",
                                    "question": "Explain Python generators.",
                                    "skill": "Python",
                                    "question_type": "technical",
                                },
                                {
                                    "id": "q2",
                                    "question": "Write a Python function.",
                                    "skill": "Python",
                                    "question_type": "coding",
                                },
                            ],
                        }
                    },
                    "evaluations": {"q1": {"score": 8}, "q2": {"score": 5}},
                },
            }
        ]

        dashboard = build_progress_dashboard(sessions)

        self.assertEqual(dashboard["overall_average"], 6.5)
        self.assertEqual(dashboard["average_by_skill"][0]["skill"], "Python")
        self.assertEqual(len(dashboard["retry_questions"]), 1)
        self.assertEqual(len(dashboard["score_trend"]), 1)

    def test_adaptive_progress_uses_only_adaptive_payload_shape(self):
        sessions = [
            {
                "id": "adaptive-1",
                "title": "AI Engineer adaptive interview",
                "created_at": "2026-01-01T00:00:00+00:00",
                "updated_at": "2026-01-02T00:00:00+00:00",
                "payload": {
                    "state": {
                        "role": "AI Engineer",
                        "learner_profile": {
                            "readiness_score": 72,
                            "strongest_skills": ["Python"],
                            "weakest_skills": ["SQL", "RAG"],
                            "skills": [
                                {"skill": "Python", "status": "strong"},
                                {"skill": "SQL", "status": "weak"},
                                {"skill": "RAG", "status": "developing"},
                            ],
                        },
                        "turns": [
                            {
                                "question": {"id": "q1", "skill": "SQL"},
                                "evaluation": {"score": 4},
                            },
                            {
                                "question": {"id": "q2", "skill": "Python"},
                                "evaluation": {"score": 8},
                            },
                        ],
                    },
                    "final_summary": {"summary": "Needs SQL practice."},
                },
            }
        ]

        dashboard = build_adaptive_progress_dashboard(sessions)

        self.assertEqual(dashboard["sessions"], 1)
        self.assertEqual(dashboard["answered_questions"], 2)
        self.assertEqual(dashboard["overall_average"], 6.0)
        self.assertEqual(dashboard["latest_readiness_score"], 72)
        self.assertEqual(dashboard["skill_status_counts"]["weak"], 1)
        self.assertEqual(dashboard["weakest_skills"], ["SQL", "RAG"])
        self.assertEqual(dashboard["recent_reports"][0]["summary"], "Needs SQL practice.")
