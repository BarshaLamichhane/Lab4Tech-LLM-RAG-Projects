from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


QuestionType = Literal["technical", "coding", "behavioral", "project", "gap", "role_fit"]
Difficulty = Literal["easy", "medium", "hard"]
InterviewEngine = Literal["mistral"]
PreparationLevel = Literal["beginner", "intermediate", "advanced"]
PreparationInterviewType = Literal[
    "technical_theory",
    "coding",
    "project",
    "behavioral",
    "mixed",
]
QuestionGenerationStrategy = Literal["llm", "grounded"]
GroundingIndexMode = Literal["use_existing", "recreate", "update"]
AdaptiveStartFocus = Literal["weak", "strong"]
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
    is_coding: bool = False
    criteria_source: Literal["llm", "template"] = "llm"
    expected_points: list[str] = Field(default_factory=list)
    expected_point_weights: list[float] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    scoring_rubric: list[str] = Field(default_factory=list)
    hint: str = ""
    requires_grounding: bool = False
    grounding_query: str | None = None
    test_cases: list[dict[str, Any]] = Field(default_factory=list)
    generation_strategy: QuestionGenerationStrategy = "llm"
    grounding_used: list[str] = Field(default_factory=list)


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


class ExpectedPointAssessment(BaseModel):
    point: str
    weight: float = Field(ge=0)
    awarded_score: float = Field(ge=0)
    explanation: str


class ScoreBreakdownItem(BaseModel):
    category: Literal[
        "technical_correctness",
        "completeness",
        "communication",
        "examples",
        "code_quality",
    ]
    label: str
    max_score: float = Field(ge=0)
    awarded_score: float = Field(ge=0)
    explanation: str


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
    expected_point_assessments: list[ExpectedPointAssessment] = Field(default_factory=list)
    score_breakdown: list[ScoreBreakdownItem] = Field(default_factory=list)
    evaluation_strategy: str = "rubric"
    execution_result: dict[str, Any] | None = None
    grounding_used: list[str] = Field(default_factory=list)


class LearningPathRequest(BaseModel):
    context: InterviewContext
    evaluations: list[AnswerEvaluation] = Field(default_factory=list)


class PreparationInterviewRequest(BaseModel):
    role: str
    selected_skills: list[str]
    candidate_projects: list[dict[str, Any]] = Field(default_factory=list)
    question_count: int = Field(default=5, ge=1, le=20)
    level: PreparationLevel = "intermediate"
    interview_type: PreparationInterviewType = "mixed"
    generation_strategy: QuestionGenerationStrategy = "llm"
    grounding_query: str | None = None
    grounding_index_mode: GroundingIndexMode = "use_existing"
    use_company_context: bool = False
    company_context: dict[str, str] | None = None


class GroundingIndexRequest(BaseModel):
    mode: GroundingIndexMode = "update"


class GroundingUrlRequest(BaseModel):
    url: str
    filename: str | None = None


class PreparationInterviewResponse(BaseModel):
    role: str
    selected_skills: list[str]
    level: PreparationLevel
    interview_type: PreparationInterviewType
    questions: list[InterviewQuestion]


class RegeneratePreparationQuestionRequest(BaseModel):
    role: str
    selected_skills: list[str]
    candidate_projects: list[dict[str, Any]] = Field(default_factory=list)
    level: PreparationLevel = "intermediate"
    interview_type: PreparationInterviewType = "mixed"
    question_id: str
    existing_questions: list[InterviewQuestion]
    use_company_context: bool = False
    company_context: dict[str, str] | None = None


class QuestionQualityReportRequest(BaseModel):
    question: InterviewQuestion
    reason: Literal["irrelevant", "incorrect", "duplicate", "poor_quality", "other"]
    comment: str = Field(default="", max_length=1000)


class AdaptiveInterviewStartRequest(BaseModel):
    role: str
    selected_skills: list[str] = Field(default_factory=list)
    level: PreparationLevel = "intermediate"
    max_turns: int = Field(default=5, ge=2, le=10)
    start_focus: AdaptiveStartFocus = "weak"
    context: InterviewContext | None = None
    generation_strategy: QuestionGenerationStrategy = "llm"
    grounding_query: str | None = None
    grounding_index_mode: GroundingIndexMode = "use_existing"
    use_company_context: bool = False
    company_context: dict[str, str] | None = None


class AdaptiveSkillProfile(BaseModel):
    skill: str
    source_group: str
    priority: float = 0
    cv_status: Literal["matched", "missing", "unknown"] = "unknown"
    job_importance: str = ""
    estimated_score: float = 5.0
    attempts: int = 0
    average_score: float | None = None
    last_score: float | None = None
    status: Literal["weak", "developing", "strong"] = "developing"


class AdaptiveLearnerProfile(BaseModel):
    goal_role: str
    readiness_score: float = 0
    skills: list[AdaptiveSkillProfile] = Field(default_factory=list)
    strongest_skills: list[str] = Field(default_factory=list)
    weakest_skills: list[str] = Field(default_factory=list)
    next_focus: str | None = None


class AdaptiveInterviewTurn(BaseModel):
    question: InterviewQuestion
    answer: str | None = None
    evaluation: AnswerEvaluation | None = None
    selected_skill: str | None = None
    decision_reason: str = ""


class AdaptiveInterviewState(BaseModel):
    role: str
    selected_skills: list[str]
    level: PreparationLevel
    max_turns: int = Field(default=5, ge=2, le=10)
    start_focus: AdaptiveStartFocus = "weak"
    context: InterviewContext | None = None
    generation_strategy: QuestionGenerationStrategy = "llm"
    grounding_query: str | None = None
    grounding_index_mode: GroundingIndexMode = "use_existing"
    use_company_context: bool = False
    company_context: dict[str, str] | None = None
    learner_profile: AdaptiveLearnerProfile | None = None
    current_skill: str | None = None
    current_decision_reason: str = ""
    turns: list[AdaptiveInterviewTurn] = Field(default_factory=list)


class AdaptiveInterviewAnswerRequest(BaseModel):
    state: AdaptiveInterviewState
    answer: str


class AdaptiveInterviewResponse(BaseModel):
    state: AdaptiveInterviewState
    next_question: InterviewQuestion | None = None
    finished: bool = False
    final_summary: dict[str, Any] | None = None


class CodeRunRequest(BaseModel):
    code: str
    stdin: str = ""
    timeout_seconds: int = 3


class CodeRunResponse(BaseModel):
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    timed_out: bool = False
