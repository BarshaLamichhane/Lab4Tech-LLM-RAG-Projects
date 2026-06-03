from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


QuestionType = Literal["technical", "behavioral", "project", "gap", "role_fit"]
Difficulty = Literal["easy", "medium", "hard"]
InterviewEngine = Literal["mistral"]
QuestionFocus = Literal[
    "all",
    "matched_strongly_required",
    "matched_skills",
    "matched_required",
    "missing_strongly_required",
    "missing_skills",
    "missing_required",
    "matched_tools",
    "missing_tools",
    "soft_skills",
    "responsibilities",
]


class InterviewContext(BaseModel):
    candidate_profile: dict[str, Any]
    job_profile: dict[str, Any]
    match_result: dict[str, Any]
    focus_skills: list[str] = Field(default_factory=list)
    gap_skills: list[str] = Field(default_factory=list)
    skill_groups: dict[str, list[str]] = Field(default_factory=dict)


class InterviewQuestion(BaseModel):
    id: str
    question: str
    question_type: QuestionType
    difficulty: Difficulty = "medium"
    skill: str | None = None
    source_group: str | None = None
    expected_points: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    scoring_rubric: list[str] = Field(default_factory=list)


class InterviewPlan(BaseModel):
    role: str
    readiness_score: float
    engine: InterviewEngine = "mistral"
    question_focus: list[QuestionFocus] = Field(default_factory=lambda: ["all"])
    selected_focus_skills: dict[QuestionFocus, list[str]] = Field(default_factory=dict)
    interview_rounds: list[str] = Field(default_factory=list)
    questions: list[InterviewQuestion] = Field(default_factory=list)
    learning_path: list[dict[str, Any]] = Field(default_factory=list)


class BuildInterviewContextRequest(BaseModel):
    cv_text: str
    job_description_text: str | None = None
    target_role: str | None = None


class EvaluateAnswerRequest(BaseModel):
    question: InterviewQuestion
    answer: str
    context: InterviewContext | None = None
    interview_engine: InterviewEngine = "mistral"


class AnswerEvaluation(BaseModel):
    score: float
    rating: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    feedback: str
    improved_answer_outline: list[str] = Field(default_factory=list)
    follow_up_question: str | None = None
    learning_recommendations: list[str] = Field(default_factory=list)


class LearningPathRequest(BaseModel):
    context: InterviewContext
    evaluations: list[AnswerEvaluation] = Field(default_factory=list)


class PreparationInterviewRequest(BaseModel):
    role: str
    selected_skills: list[str]
    question_count: int = 5
    level: str = "intermediate"


class PreparationInterviewResponse(BaseModel):
    role: str
    selected_skills: list[str]
    questions: list[InterviewQuestion]


class AdaptiveInterviewStartRequest(BaseModel):
    role: str
    selected_skills: list[str]
    level: str = "intermediate"


class AdaptiveInterviewTurn(BaseModel):
    question: str
    answer: str | None = None
    feedback: str | None = None
    score: float | None = None


class AdaptiveInterviewState(BaseModel):
    role: str
    selected_skills: list[str]
    level: str
    turns: list[AdaptiveInterviewTurn] = Field(default_factory=list)


class AdaptiveInterviewAnswerRequest(BaseModel):
    state: AdaptiveInterviewState
    answer: str


class AdaptiveInterviewResponse(BaseModel):
    state: AdaptiveInterviewState
    next_question: str | None = None
    finished: bool = False
    final_summary: str | None = None


class CodeRunRequest(BaseModel):
    code: str
    stdin: str = ""
    timeout_seconds: int = 3


class CodeRunResponse(BaseModel):
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    timed_out: bool = False
