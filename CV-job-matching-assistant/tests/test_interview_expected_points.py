from unittest import TestCase

from backend.interview.expected_point_templates import python_expected_point_template
from backend.interview.preparation_interview import _validated_question


def python_generator_question(expected_points: list[str]) -> dict:
    return {
        "id": "q1",
        "question": "Explain how Python generators process large datasets efficiently.",
        "question_type": "technical",
        "difficulty": "medium",
        "skill": "Python",
        "source_group": "selected_skills",
        "is_coding": False,
        "expected_points": expected_points,
        "follow_up_questions": ["When would you avoid a Python generator?"],
        "scoring_rubric": [
            "Explains Python lazy evaluation",
            "Explains relevant Python trade-offs",
        ],
        "hint": "Think about producing one value at a time.",
    }


class InterviewExpectedPointTests(TestCase):
    def test_applies_reviewed_python_generator_template(self):
        question = _validated_question(
            python_generator_question(
                [
                    "Explains Python lazy iteration",
                    "Explains Python memory benefits",
                ]
            ),
            selected_skills=["Python"],
            level="intermediate",
            interview_type="technical_theory",
        )

        self.assertIsNotNone(question)
        self.assertEqual(question.criteria_source, "template")
        self.assertIn("yield", " ".join(question.expected_points).casefold())
        self.assertEqual(len(question.expected_point_weights), len(question.expected_points))
        self.assertEqual(sum(question.expected_point_weights), 10.0)

    def test_rejects_unrelated_library_in_expected_points(self):
        question = _validated_question(
            python_generator_question(
                [
                    "Explains Python lazy iteration",
                    "Uses pandas for efficient processing",
                ]
            ),
            selected_skills=["Python"],
            level="intermediate",
            interview_type="technical_theory",
        )

        self.assertIsNone(question)

    def test_allows_library_explicitly_named_in_question(self):
        raw_question = python_generator_question(
            [
                "Explains Python lazy iteration",
                "Explains how pandas participates in the solution",
            ]
        )
        raw_question["question"] = (
            "Compare Python generators with pandas when processing a large dataset."
        )

        question = _validated_question(
            raw_question,
            selected_skills=["Python"],
            level="intermediate",
            interview_type="technical_theory",
        )

        self.assertIsNotNone(question)

    def test_unknown_python_topic_has_no_template(self):
        self.assertIsNone(
            python_expected_point_template("Python", "Explain Python descriptor behavior.")
        )
