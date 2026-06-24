from unittest import TestCase

from backend.interview.preparation_interview import _validated_question
from backend.interview.python_test_case_templates import (
    python_test_cases_for_question,
    validate_python_test_cases,
)


def coding_question(question: str) -> dict:
    return {
        "id": "q1",
        "question": question,
        "question_type": "coding",
        "difficulty": "medium",
        "skill": "Python",
        "source_group": "selected_skills",
        "is_coding": True,
        "expected_points": ["Returns the correct result", "Handles edge cases"],
        "follow_up_questions": ["What is the time complexity?"],
        "scoring_rubric": ["Correctness", "Code quality"],
        "hint": "Start with a function.",
    }


class PythonTestCaseTemplateTests(TestCase):
    def test_generates_deterministic_even_number_cases(self):
        test_cases = python_test_cases_for_question(
            "Python",
            "Write a Python function that returns only even numbers from a list.",
        )

        self.assertEqual(len(test_cases), 3)
        self.assertEqual(test_cases[0]["expected_output"], [2, 4, 6])

    def test_does_not_generate_cases_for_unknown_or_non_python_topic(self):
        self.assertEqual(
            python_test_cases_for_question("Python", "Write a Python context manager."),
            [],
        )
        self.assertEqual(
            python_test_cases_for_question("Java", "Return only even numbers."),
            [],
        )

    def test_rejects_malformed_test_cases(self):
        valid = validate_python_test_cases(
            [
                {"args": [2], "expected_output": True},
                {"args": "not-a-list", "expected_output": True},
                {"input": "hello\n"},
                "invalid",
            ]
        )

        self.assertEqual(valid, [{"args": [2], "expected_output": True}])

    def test_validated_coding_question_receives_deterministic_cases(self):
        question = _validated_question(
            coding_question(
                "Write a Python function that returns only even numbers from a list."
            ),
            selected_skills=["Python"],
            level="intermediate",
            interview_type="coding",
        )

        self.assertIsNotNone(question)
        self.assertEqual(len(question.test_cases), 3)
