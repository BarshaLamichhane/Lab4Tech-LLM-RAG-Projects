from unittest import TestCase

from backend.interview.interview_assistant import (
    NON_CODING_SCORE_BUDGET,
    _validated_evaluation,
)
from backend.interview.schemas import InterviewQuestion


QUESTION = InterviewQuestion(
    id="q1",
    question="Explain Python generators and their memory benefits.",
    question_type="technical",
    difficulty="medium",
    skill="Python",
    expected_points=[
        "Explains lazy iteration",
        "Explains memory benefits",
    ],
    expected_point_weights=[5.0, 5.0],
    scoring_rubric=["Correct explanation", "Relevant trade-offs"],
)


def evaluation_payload(category_ratio: float, point_ratio: float = 1.0) -> dict:
    return {
        "score": 10,
        "rating": "Strong",
        "strengths": ["Relevant explanation"],
        "weaknesses": [],
        "missing_points": [],
        "feedback": "Calibration response",
        "improved_answer_outline": ["Explain the mechanism", "Explain trade-offs"],
        "follow_up_question": "When would you avoid a generator?",
        "learning_recommendations": ["Python generators"],
        "expected_point_assessments": [
            {
                "point": point,
                "weight": weight,
                "awarded_score": weight * point_ratio,
                "explanation": "Evidence-based point assessment",
            }
            for point, weight in zip(QUESTION.expected_points, QUESTION.expected_point_weights)
        ],
        "score_breakdown": [
            {
                "category": category,
                "label": label,
                "max_score": maximum,
                "awarded_score": maximum * category_ratio,
                "explanation": "Evidence-based category assessment",
            }
            for category, (label, maximum) in NON_CODING_SCORE_BUDGET.items()
        ],
    }


class InterviewScoringReliabilityTests(TestCase):
    def score(self, category_ratio: float, point_ratio: float = 1.0) -> float:
        return _validated_evaluation(
            evaluation_payload(category_ratio, point_ratio),
            QUESTION,
            QUESTION.expected_point_weights,
            NON_CODING_SCORE_BUDGET,
        ).score

    def test_strong_average_and_weak_answers_are_ordered(self):
        strong = self.score(0.9)
        average = self.score(0.6)
        weak = self.score(0.2)

        self.assertGreater(strong, average)
        self.assertGreater(average, weak)
        self.assertEqual(strong, 9.0)
        self.assertEqual(average, 6.0)
        self.assertEqual(weak, 2.0)

    def test_final_score_is_calculated_from_category_breakdown(self):
        payload = evaluation_payload(0.7, 1.0)
        payload["score"] = 0

        evaluation = _validated_evaluation(
            payload,
            QUESTION,
            QUESTION.expected_point_weights,
            NON_CODING_SCORE_BUDGET,
        )

        self.assertEqual(evaluation.score, 7.0)
        self.assertEqual(evaluation.rating, "Good")

    def test_awarded_scores_are_clamped_to_fixed_budgets(self):
        payload = evaluation_payload(1.0)
        for item in payload["score_breakdown"]:
            item["awarded_score"] = 100

        evaluation = _validated_evaluation(
            payload,
            QUESTION,
            QUESTION.expected_point_weights,
            NON_CODING_SCORE_BUDGET,
        )

        self.assertEqual(evaluation.score, 10.0)
        self.assertTrue(
            all(item.awarded_score <= item.max_score for item in evaluation.score_breakdown)
        )
