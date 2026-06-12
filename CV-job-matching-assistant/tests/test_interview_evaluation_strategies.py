from unittest import TestCase
from unittest.mock import patch

from backend.interview.interview_assistant import (
    CODING_SCORE_BUDGET,
    NON_CODING_SCORE_BUDGET,
    _run_python_test_evaluation,
    _validated_evaluation,
    select_evaluation_strategy,
)
from backend.interview.grounding_retriever import retrieve_grounding_context
from backend.interview.schemas import InterviewContext, InterviewQuestion
from tests.test_interview_scoring_reliability import evaluation_payload


def question(**updates) -> InterviewQuestion:
    values = {
        "id": "q1",
        "question": "Write Python code that echoes standard input.",
        "question_type": "coding",
        "difficulty": "easy",
        "skill": "Python",
        "is_coding": True,
        "expected_points": ["Produces the expected output", "Uses valid code"],
        "expected_point_weights": [5.0, 5.0],
        "scoring_rubric": ["Correctness", "Code quality"],
    }
    values.update(updates)
    return InterviewQuestion(**values)


class EvaluationStrategySelectionTests(TestCase):
    def test_python_and_sql_coding_use_test_based(self):
        self.assertEqual(select_evaluation_strategy(question()), "test_based")
        self.assertEqual(select_evaluation_strategy(question(skill="SQL")), "test_based")

    def test_framework_and_explicit_grounding_use_grounded(self):
        self.assertEqual(
            select_evaluation_strategy(question(skill="LangChain", is_coding=False)),
            "grounded",
        )
        self.assertEqual(
            select_evaluation_strategy(question(skill="Python", is_coding=False, requires_grounding=True)),
            "grounded",
        )

    def test_general_question_uses_rubric(self):
        self.assertEqual(
            select_evaluation_strategy(question(skill="Python", is_coding=False)),
            "rubric",
        )


class PythonTestBasedScoringTests(TestCase):
    def test_passing_and_failing_test_cases_are_collected(self):
        test_question = question(
            test_cases=[
                {"input": "hello\n", "expected_output": "hello"},
                {"input": "world\n", "expected_output": "different"},
            ]
        )

        result, score_cap = _run_python_test_evaluation(
            test_question,
            "```python\nprint(input())\n```",
        )

        self.assertEqual(result["passed"], 1)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(score_cap, 10.0)

    def test_runtime_error_caps_score_at_four(self):
        result, score_cap = _run_python_test_evaluation(
            question(test_cases=[{"input": "", "expected_output": "ok"}]),
            "```python\nraise RuntimeError('failed')\n```",
        )

        self.assertEqual(result["failed"], 1)
        self.assertEqual(score_cap, 4.0)

    def test_function_submission_is_run_against_argument_test_cases(self):
        test_question = question(
            question="Write a Python function that returns only even numbers.",
            test_cases=[
                {"args": [[1, 2, 3, 4]], "expected_output": [2, 4]},
                {"args": [[1, 3]], "expected_output": []},
            ],
        )

        result, score_cap = _run_python_test_evaluation(
            test_question,
            "def filter_even(values):\n    return [value for value in values if value % 2 == 0]",
        )

        self.assertEqual(result["passed"], 2)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(score_cap, 10.0)

    def test_failing_most_tests_caps_score_at_six(self):
        result, score_cap = _run_python_test_evaluation(
            question(
                test_cases=[
                    {"input": "one\n", "expected_output": "one"},
                    {"input": "two\n", "expected_output": "wrong"},
                    {"input": "three\n", "expected_output": "wrong"},
                ]
            ),
            "```python\nprint(input())\n```",
        )

        self.assertEqual(result["passed"], 1)
        self.assertEqual(result["failed"], 2)
        self.assertEqual(score_cap, 6.0)

    def test_score_cap_is_applied_to_score_breakdown(self):
        payload = evaluation_payload(1.0)
        evaluation = _validated_evaluation(
            payload,
            question(),
            [5.0, 5.0],
            CODING_SCORE_BUDGET,
            evaluation_strategy="test_based",
            execution_result={"failed": 1},
            score_cap=4.0,
        )

        self.assertEqual(evaluation.score, 4.0)
        self.assertEqual(
            evaluation.score,
            round(sum(item.awarded_score for item in evaluation.score_breakdown), 1),
        )
        self.assertEqual(evaluation.evaluation_strategy, "test_based")


class GroundedScoringTests(TestCase):
    @patch("backend.interview.grounding_retriever.retrieve_faiss_context")
    def test_retrieves_from_shared_faiss_service_and_tracks_source(self, retrieve):
        retrieve.return_value = [
            {
                "source": "langchain-docs.md",
                "text": "LangChain connects tools to agents.",
            }
        ]
        grounded_question = question(
            question="How does LangChain connect tools?",
            skill="LangChain",
            is_coding=False,
            requires_grounding=True,
        )
        context = InterviewContext(
            candidate_profile={},
            job_profile={"skills": ["LangChain"], "notes": "LangChain connects tools to agents."},
            match_result={},
        )

        retrieved, sources = retrieve_grounding_context(grounded_question, context)

        retrieve.assert_called_once_with(
            "LangChain How does LangChain connect tools?",
            top_k=5,
        )
        self.assertEqual(retrieved, ["LangChain connects tools to agents."])
        self.assertEqual(sources, ["langchain-docs.md"])

    def test_grounding_sources_are_returned_in_evaluation(self):
        payload = evaluation_payload(0.8)
        evaluation = _validated_evaluation(
            payload,
            question(skill="LangChain", is_coding=False),
            [5.0, 5.0],
            NON_CODING_SCORE_BUDGET,
            evaluation_strategy="grounded",
            grounding_used=["learning-material.md"],
        )

        self.assertEqual(evaluation.evaluation_strategy, "grounded")
        self.assertEqual(evaluation.grounding_used, ["learning-material.md"])
