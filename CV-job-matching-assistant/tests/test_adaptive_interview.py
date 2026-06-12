import json
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from backend.interview.adaptive_interview import (
    _next_difficulty,
    _normalized_final_summary,
    start_adaptive_interview,
    submit_adaptive_answer,
)
from backend.interview.schemas import (
    AdaptiveInterviewAnswerRequest,
    AdaptiveInterviewStartRequest,
    AdaptiveInterviewState,
    AdaptiveInterviewTurn,
    AnswerEvaluation,
    InterviewQuestion,
)


def question(difficulty: str = "medium") -> InterviewQuestion:
    return InterviewQuestion(
        id="adaptive-1",
        question="Explain Python generators.",
        question_type="technical",
        difficulty=difficulty,
        skill="Python",
        expected_points=["Explains yield", "Explains lazy evaluation"],
        expected_point_weights=[5, 5],
        follow_up_questions=["When would you avoid one?"],
        scoring_rubric=["Correctness", "Trade-offs"],
        hint="Think about values produced one at a time.",
    )


def evaluation(score: float) -> AnswerEvaluation:
    return AnswerEvaluation(score=score, rating="Good", feedback="Feedback")


def response_payload() -> SimpleNamespace:
    payload = {"question": question().model_dump(mode="json")}
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))]
    )


class AdaptiveInterviewTests(TestCase):
    def test_normalizes_structured_summary_recommendations(self):
        result = _normalized_final_summary(
            {
                "summary": "Keep practising.",
                "recommended_next_steps": [
                    {
                        "focus_area": "Generators",
                        "action": "Build a streaming parser",
                        "resources": ["Python docs", "Exercises"],
                    }
                ],
            }
        )

        self.assertIsInstance(result["recommended_next_steps"][0], str)
        self.assertIn("Focus Area: Generators", result["recommended_next_steps"][0])

    def test_requires_exactly_one_skill(self):
        with self.assertRaisesRegex(ValueError, "exactly one"):
            start_adaptive_interview(
                AdaptiveInterviewStartRequest(role="AI Engineer", selected_skills=["Python", "SQL"])
            )

    @patch("backend.interview.adaptive_interview._complete_mistral_chat")
    def test_starts_with_structured_question(self, complete):
        complete.return_value = response_payload()

        result = start_adaptive_interview(
            AdaptiveInterviewStartRequest(role="AI Engineer", selected_skills=["Python"])
        )

        self.assertEqual(result.next_question.skill, "Python")
        self.assertEqual(len(result.state.turns), 1)

    def test_difficulty_adapts_from_validated_score(self):
        state = AdaptiveInterviewState(
            role="AI Engineer",
            selected_skills=["Python"],
            level="intermediate",
            turns=[AdaptiveInterviewTurn(question=question(), answer="answer", evaluation=evaluation(9))],
        )
        self.assertEqual(_next_difficulty(state), "hard")
        state.turns[-1].evaluation = evaluation(3)
        self.assertEqual(_next_difficulty(state), "easy")

    @patch("backend.interview.adaptive_interview._generate_final_summary")
    @patch("backend.interview.adaptive_interview.evaluate_answer")
    def test_final_turn_uses_existing_evaluation_engine(self, evaluate, summary):
        evaluate.return_value = evaluation(8)
        summary.return_value = {"summary": "Ready"}
        state = AdaptiveInterviewState(
            role="AI Engineer",
            selected_skills=["Python"],
            level="intermediate",
            max_turns=2,
            turns=[
                AdaptiveInterviewTurn(question=question(), answer="first", evaluation=evaluation(7)),
                AdaptiveInterviewTurn(question=question()),
            ],
        )

        result = submit_adaptive_answer(
            AdaptiveInterviewAnswerRequest(state=state, answer="second answer")
        )

        evaluate.assert_called_once()
        self.assertTrue(result.finished)
        self.assertEqual(result.final_summary["summary"], "Ready")

    @patch("backend.interview.adaptive_interview._generate_final_summary")
    @patch("backend.interview.adaptive_interview.evaluate_answer")
    def test_final_turn_falls_back_when_summary_generation_fails(self, evaluate, summary):
        evaluate.return_value = evaluation(8)
        summary.side_effect = RuntimeError("summary unavailable")
        state = AdaptiveInterviewState(
            role="AI Engineer",
            selected_skills=["Python"],
            level="intermediate",
            max_turns=2,
            turns=[
                AdaptiveInterviewTurn(question=question(), answer="first", evaluation=evaluation(7)),
                AdaptiveInterviewTurn(question=question()),
            ],
        )

        result = submit_adaptive_answer(
            AdaptiveInterviewAnswerRequest(state=state, answer="second answer")
        )

        self.assertTrue(result.finished)
        self.assertIn("average score", result.final_summary["summary"])
