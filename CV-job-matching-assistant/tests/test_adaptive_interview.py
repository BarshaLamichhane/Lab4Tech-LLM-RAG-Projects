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
    InterviewContext,
    InterviewQuestion,
)


def question(difficulty: str = "medium", skill: str = "Python") -> InterviewQuestion:
    return InterviewQuestion(
        id="adaptive-1",
        question=f"Explain {skill} interview fundamentals.",
        question_type="technical",
        difficulty=difficulty,
        skill=skill,
        expected_points=["Explains yield", "Explains lazy evaluation"],
        expected_point_weights=[5, 5],
        follow_up_questions=["When would you avoid one?"],
        scoring_rubric=["Correctness", "Trade-offs"],
        hint="Think about values produced one at a time.",
    )


def evaluation(score: float) -> AnswerEvaluation:
    return AnswerEvaluation(score=score, rating="Good", feedback="Feedback")


def context() -> InterviewContext:
    return InterviewContext(
        candidate_profile={},
        job_profile={},
        match_result={"score": 62},
        skill_groups={
            "missing_strongly_required": ["SQL"],
            "missing_required": ["RAG"],
            "matched_strongly_required": ["Python"],
            "matched_tools": ["Docker"],
        },
    )


def response_payload(skill: str = "SQL", difficulty: str = "medium") -> SimpleNamespace:
    payload = {"question": question(skill=skill, difficulty=difficulty).model_dump(mode="json")}
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

    def test_requires_cv_role_context(self):
        with self.assertRaisesRegex(ValueError, "CV-to-role comparison"):
            start_adaptive_interview(
                AdaptiveInterviewStartRequest(role="AI Engineer")
            )

    @patch("backend.interview.adaptive_interview._complete_mistral_chat")
    def test_starts_from_highest_priority_weak_skill(self, complete):
        complete.return_value = response_payload()

        result = start_adaptive_interview(
            AdaptiveInterviewStartRequest(role="AI Engineer", context=context())
        )

        self.assertEqual(result.next_question.skill, "SQL")
        self.assertEqual(result.state.current_skill, "SQL")
        self.assertIn("SQL", result.state.learner_profile.weakest_skills)
        self.assertEqual(len(result.state.turns), 1)

    @patch("backend.interview.adaptive_interview._complete_mistral_chat")
    def test_can_start_from_highest_priority_strong_skill(self, complete):
        complete.return_value = response_payload("Python")

        result = start_adaptive_interview(
            AdaptiveInterviewStartRequest(role="AI Engineer", context=context(), start_focus="strong")
        )

        self.assertEqual(result.next_question.skill, "Python")
        self.assertEqual(result.state.start_focus, "strong")
        self.assertIn("validating a strength", result.state.current_decision_reason)

    @patch("backend.interview.adaptive_interview._complete_mistral_chat")
    def test_uses_fallback_question_when_mistral_generation_fails(self, complete):
        complete.side_effect = RuntimeError("Mistral request failed")

        result = start_adaptive_interview(
            AdaptiveInterviewStartRequest(role="AI Engineer", context=context())
        )

        self.assertEqual(result.next_question.skill, "SQL")
        self.assertIn("SQL", result.next_question.question)
        self.assertEqual(result.next_question.criteria_source, "template")

    def test_difficulty_adapts_from_validated_score(self):
        state = AdaptiveInterviewState(
            role="AI Engineer",
            selected_skills=["Python"],
            level="intermediate",
            context=context(),
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
            context=context(),
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
            context=context(),
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

    @patch("backend.interview.adaptive_interview._complete_mistral_chat")
    @patch("backend.interview.adaptive_interview.evaluate_answer")
    def test_weak_answer_stays_on_same_skill(self, evaluate, complete):
        evaluate.return_value = evaluation(3)
        complete.side_effect = [response_payload("SQL"), response_payload("SQL", "easy")]
        session = start_adaptive_interview(
            AdaptiveInterviewStartRequest(role="AI Engineer", context=context(), max_turns=3)
        )

        result = submit_adaptive_answer(
            AdaptiveInterviewAnswerRequest(state=session.state, answer="weak answer")
        )

        self.assertFalse(result.finished)
        self.assertEqual(result.next_question.skill, "SQL")
        self.assertIn("stayed weak", result.state.current_decision_reason)

    @patch("backend.interview.adaptive_interview._complete_mistral_chat")
    @patch("backend.interview.adaptive_interview.evaluate_answer")
    def test_strong_answer_moves_to_next_weak_skill(self, evaluate, complete):
        evaluate.return_value = evaluation(9)
        complete.side_effect = [response_payload("SQL"), response_payload("RAG", "hard")]
        session = start_adaptive_interview(
            AdaptiveInterviewStartRequest(role="AI Engineer", context=context(), max_turns=3)
        )

        result = submit_adaptive_answer(
            AdaptiveInterviewAnswerRequest(state=session.state, answer="strong answer")
        )

        self.assertFalse(result.finished)
        self.assertEqual(result.next_question.skill, "RAG")
        self.assertEqual(result.state.learner_profile.skills[0].last_score, 9)
