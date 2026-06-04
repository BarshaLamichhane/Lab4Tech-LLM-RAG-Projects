from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.app.schemas import (
    ExtractJobSkillsRequest,
    ExtractJobSkillsResponse,
    MatchNewJobRequest,
    MatchResponse,
    MatchSavedJobRequest,
)
from backend.app.services import (
    build_new_job_match,
    build_saved_job_match,
    extract_job_profile,
    load_roles,
    read_uploaded_text,
)
from backend.interview.adaptive_interview import (
    start_adaptive_interview,
    submit_adaptive_answer,
)
from backend.interview.code_runner import run_python_code
from backend.interview.interview_assistant import (
    build_interview_context,
    build_learning_path,
    evaluate_answer,
)
from backend.interview.preparation_interview import generate_preparation_interview
from backend.interview.schemas import (
    AdaptiveInterviewAnswerRequest,
    AdaptiveInterviewResponse,
    AdaptiveInterviewStartRequest,
    AnswerEvaluation,
    BuildInterviewContextRequest,
    CodeRunRequest,
    CodeRunResponse,
    EvaluateAnswerRequest,
    InterviewContext,
    LearningPathRequest,
    PreparationInterviewRequest,
    PreparationInterviewResponse,
)


app = FastAPI(title="CV Job Matching Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/job-roles")
def get_job_roles() -> dict[str, list[str]]:
    return {"roles": load_roles()}


@app.post("/api/match/saved-job", response_model=MatchResponse)
def match_saved_job(request: MatchSavedJobRequest) -> dict:
    try:
        return build_saved_job_match(
            cv_text=request.cv_text,
            target_role=request.target_role,
            include_all_saved_jobs=request.include_all_saved_jobs,
            skill_weights=request.skill_weights.model_dump() if request.skill_weights else None,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/match/new-job", response_model=MatchResponse)
def match_new_job(request: MatchNewJobRequest) -> dict:
    try:
        return build_new_job_match(
            cv_text=request.cv_text,
            job_description_text=request.job_description_text,
            save_new_job_profile=request.save_new_job_profile,
            include_all_saved_jobs=request.include_all_saved_jobs,
            skill_weights=request.skill_weights.model_dump() if request.skill_weights else None,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/job-skills/extract", response_model=ExtractJobSkillsResponse)
def extract_job_skills_from_text(request: ExtractJobSkillsRequest) -> dict:
    try:
        job_profile, saved_path = extract_job_profile(
            request.job_description_text,
            save_job_profile=request.save_job_profile,
        )
        return {
            "job_profile": job_profile,
            "saved_path": str(saved_path) if saved_path else None,
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/uploads/cv-text")
async def upload_cv_text(file: UploadFile = File(...)) -> dict[str, str]:
    try:
        return {"text": await read_uploaded_text(file)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/uploads/job-description-text")
async def upload_job_description_text(file: UploadFile = File(...)) -> dict[str, str]:
    try:
        return {"text": await read_uploaded_text(file)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/match/saved-job/upload", response_model=MatchResponse)
async def match_saved_job_upload(
    target_role: str = Form(...),
    include_all_saved_jobs: bool = Form(False),
    cv_file: UploadFile = File(...),
) -> dict:
    try:
        cv_text = await read_uploaded_text(cv_file)
        return build_saved_job_match(
            cv_text=cv_text,
            target_role=target_role,
            include_all_saved_jobs=include_all_saved_jobs,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/interview/context", response_model=InterviewContext)
def create_interview_context(request: BuildInterviewContextRequest) -> InterviewContext:
    try:
        return build_interview_context(
            cv_text=request.cv_text,
            job_description_text=request.job_description_text,
            target_role=request.target_role,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/interview/evaluate-answer", response_model=AnswerEvaluation)
def evaluate_interview_answer(request: EvaluateAnswerRequest) -> AnswerEvaluation:
    try:
        return evaluate_answer(
            question=request.question,
            answer=request.answer,
            context=request.context,
            interview_engine="mistral",
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/interview/learning-path")
def create_learning_path(request: LearningPathRequest) -> list[dict]:
    try:
        return build_learning_path(
            context=request.context,
            evaluations=request.evaluations,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/interview/preparation", response_model=PreparationInterviewResponse)
def create_preparation_interview(
    request: PreparationInterviewRequest,
) -> PreparationInterviewResponse:
    try:
        return generate_preparation_interview(
            role=request.role,
            selected_skills=request.selected_skills,
            question_count=request.question_count,
            level=request.level,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/interview/adaptive/start", response_model=AdaptiveInterviewResponse)
def start_adaptive_interview_route(
    request: AdaptiveInterviewStartRequest,
) -> AdaptiveInterviewResponse:
    try:
        return start_adaptive_interview(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/interview/adaptive/answer", response_model=AdaptiveInterviewResponse)
def submit_adaptive_answer_route(
    request: AdaptiveInterviewAnswerRequest,
) -> AdaptiveInterviewResponse:
    try:
        return submit_adaptive_answer(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/interview/code/run", response_model=CodeRunResponse)
def run_interview_code(request: CodeRunRequest) -> CodeRunResponse:
    try:
        return run_python_code(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
