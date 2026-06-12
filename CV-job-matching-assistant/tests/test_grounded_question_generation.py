import json
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from backend.interview.preparation_interview import (
    _build_prompt,
    generate_preparation_interview,
)


RAW_QUESTION = {
    "id": "q1",
    "question": "According to verified material, how does LangChain connect tools?",
    "question_type": "technical",
    "difficulty": "medium",
    "skill": "LangChain",
    "source_group": "selected_skills",
    "is_coding": False,
    "expected_points": [
        "Explains the verified tool connection behavior",
        "Describes the documented control flow",
    ],
    "follow_up_questions": ["How would you verify this behavior?"],
    "scoring_rubric": ["Uses verified details", "Explains the flow"],
    "hint": "Focus on the documented connection mechanism.",
}


def mistral_response(question: dict) -> SimpleNamespace:
    content = json.dumps({"questions": [question]})
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


class GroundedQuestionGenerationTests(TestCase):
    def test_default_prompt_does_not_include_grounding(self):
        prompt = _build_prompt(
            role="AI Engineer",
            selected_skills=["Python"],
            question_count=1,
            level="intermediate",
            interview_type="technical_theory",
            candidate_projects=[],
            existing_questions=[],
        )

        self.assertNotIn("Grounding context:", prompt)
        self.assertNotIn("Generation strategy:", prompt)

    @patch("backend.interview.preparation_interview.ensure_grounding_index")
    def test_grounded_generation_requires_context(self, ensure_index):
        ensure_index.side_effect = ValueError(
            "Grounding FAISS index does not exist. Choose recreate or update."
        )
        with self.assertRaisesRegex(
            ValueError,
            "Grounding FAISS index does not exist. Choose recreate or update.",
        ):
            generate_preparation_interview(
                role="AI Engineer",
                selected_skills=["LangChain"],
                question_count=1,
                level="intermediate",
                interview_type="technical_theory",
                generation_strategy="grounded",
            )

    @patch("backend.interview.preparation_interview._complete_mistral_chat")
    @patch("backend.interview.preparation_interview.retrieve_grounding_context")
    @patch("backend.interview.preparation_interview.ensure_grounding_index")
    def test_grounded_generation_attaches_sources(
        self,
        ensure_index,
        retrieve_context,
        complete_chat,
    ):
        ensure_index.return_value = {"mode": "use_existing"}
        retrieve_context.return_value = [
            {"source": "official-langchain.md", "text": "LangChain connects tools to agents."}
        ]
        complete_chat.return_value = mistral_response(RAW_QUESTION)

        response = generate_preparation_interview(
            role="AI Engineer",
            selected_skills=["LangChain"],
            question_count=1,
            level="intermediate",
            interview_type="technical_theory",
            generation_strategy="grounded",
            grounding_query="verified LangChain tool connection",
        )

        question = response.questions[0]
        self.assertEqual(question.generation_strategy, "grounded")
        self.assertIn("official-langchain.md", question.grounding_used[0])
        prompt = complete_chat.call_args.kwargs["user_prompt"]
        self.assertIn("Grounding context:", prompt)
        self.assertIn("LangChain connects tools to agents.", prompt)
