from unittest import TestCase

from backend.interview.preparation_interview import _questions_are_similar
from backend.interview.progress_dashboard import build_progress_dashboard


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
