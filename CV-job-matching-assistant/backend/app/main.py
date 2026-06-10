from __future__ import annotations

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.app.schemas import (
    AppSettings,
    ExtractJobSkillsRequest,
    ExtractJobSkillsResponse,
    LoginRequest,
    LoginResponse,
    MatchNewJobRequest,
    MatchResponse,
    MatchSavedJobRequest,
)
from backend.app.auth import CurrentUser, login, require_user
from backend.app.session_store import load_user_sessions, save_user_session
from backend.app.settings_store import load_app_settings, save_app_settings
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
from backend.cv.cv_skill_extractor import load_skill_categories as load_cv_skill_categories
from backend.matching.skill_matching_engine import load_skill_categories as load_matching_skill_categories


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


@app.post("/api/auth/login", response_model=LoginResponse)
def login_route(request: LoginRequest) -> LoginResponse:
    token, user = login(request.username, request.password)
    return LoginResponse(token=token, username=user.username, role=user.role)


@app.get("/api/auth/me")
def current_user_route(user: CurrentUser = Depends(require_user)) -> dict[str, str]:
    return {"username": user.username, "role": user.role}


@app.get("/api/admin/settings", response_model=AppSettings)
def get_admin_settings(user: CurrentUser = Depends(require_user)) -> dict:
    _ensure_admin(user)
    return load_app_settings()


@app.put("/api/admin/settings", response_model=AppSettings)
def update_admin_settings(
    request: AppSettings,
    user: CurrentUser = Depends(require_user),
) -> dict:
    _ensure_admin(user)
    saved = save_app_settings(request.model_dump())
    load_cv_skill_categories.cache_clear()
    load_matching_skill_categories.cache_clear()
    return saved


@app.get("/api/sessions")
def get_user_sessions(user: CurrentUser = Depends(require_user)) -> list[dict]:
    return load_user_sessions(user.username)


@app.get("/api/job-roles")
def get_job_roles(user: CurrentUser = Depends(require_user)) -> dict[str, list[str]]:
    return {"roles": load_roles()}


@app.post("/api/match/saved-job", response_model=MatchResponse)
def match_saved_job(
    request: MatchSavedJobRequest,
    user: CurrentUser = Depends(require_user),
) -> dict:
    try:
        result = build_saved_job_match(
            cv_text=request.cv_text,
            target_role=request.target_role,
            include_all_saved_jobs=request.include_all_saved_jobs,
            skill_weights=_resolve_skill_weights(request.skill_weights, user),
        )
        save_user_session(user.username, "saved_job_match", request.target_role, result)
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/match/new-job", response_model=MatchResponse)
def match_new_job(
    request: MatchNewJobRequest,
    user: CurrentUser = Depends(require_user),
) -> dict:
    try:
        result = build_new_job_match(
            cv_text=request.cv_text,
            job_description_text=request.job_description_text,
            save_new_job_profile=request.save_new_job_profile,
            include_all_saved_jobs=request.include_all_saved_jobs,
            skill_weights=_resolve_skill_weights(request.skill_weights, user),
        )
        title = result.get("target_job_match", {}).get("target_role", "New job match")
        save_user_session(user.username, "new_job_match", title, result)
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/job-skills/extract", response_model=ExtractJobSkillsResponse)
def extract_job_skills_from_text(
    request: ExtractJobSkillsRequest,
    user: CurrentUser = Depends(require_user),
) -> dict:
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
async def upload_cv_text(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_user),
) -> dict[str, str]:
    try:
        return {"text": await read_uploaded_text(file)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/uploads/job-description-text")
async def upload_job_description_text(
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_user),
) -> dict[str, str]:
    try:
        return {"text": await read_uploaded_text(file)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/match/saved-job/upload", response_model=MatchResponse)
async def match_saved_job_upload(
    target_role: str = Form(...),
    include_all_saved_jobs: bool = Form(False),
    cv_file: UploadFile = File(...),
    user: CurrentUser = Depends(require_user),
) -> dict:
    try:
        cv_text = await read_uploaded_text(cv_file)
        result = build_saved_job_match(
            cv_text=cv_text,
            target_role=target_role,
            include_all_saved_jobs=include_all_saved_jobs,
            skill_weights=_resolve_skill_weights(None, user),
        )
        save_user_session(user.username, "saved_job_match", target_role, result)
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/interview/context", response_model=InterviewContext)
def create_interview_context(
    request: BuildInterviewContextRequest,
    user: CurrentUser = Depends(require_user),
) -> InterviewContext:
    try:
        return build_interview_context(
            cv_text=request.cv_text,
            job_description_text=request.job_description_text,
            target_role=request.target_role,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/interview/evaluate-answer", response_model=AnswerEvaluation)
def evaluate_interview_answer(
    request: EvaluateAnswerRequest,
    user: CurrentUser = Depends(require_user),
) -> AnswerEvaluation:
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
def create_learning_path(
    request: LearningPathRequest,
    user: CurrentUser = Depends(require_user),
) -> list[dict]:
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
    user: CurrentUser = Depends(require_user),
) -> PreparationInterviewResponse:
    try:
        result = generate_preparation_interview(
            role=request.role,
            selected_skills=request.selected_skills,
            question_count=request.question_count,
            level=request.level,
        )
        save_user_session(
            user.username,
            "interview_preparation",
            request.role,
            result.model_dump(),
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/interview/adaptive/start", response_model=AdaptiveInterviewResponse)
def start_adaptive_interview_route(
    request: AdaptiveInterviewStartRequest,
    user: CurrentUser = Depends(require_user),
) -> AdaptiveInterviewResponse:
    try:
        return start_adaptive_interview(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/interview/adaptive/answer", response_model=AdaptiveInterviewResponse)
def submit_adaptive_answer_route(
    request: AdaptiveInterviewAnswerRequest,
    user: CurrentUser = Depends(require_user),
) -> AdaptiveInterviewResponse:
    try:
        return submit_adaptive_answer(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/interview/code/run", response_model=CodeRunResponse)
def run_interview_code(
    request: CodeRunRequest,
    user: CurrentUser = Depends(require_user),
) -> CodeRunResponse:
    try:
        return run_python_code(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _ensure_admin(user: CurrentUser) -> None:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")


def _resolve_skill_weights(request_weights, user: CurrentUser) -> dict[str, float]:
    if user.role == "admin" and request_weights:
        return request_weights.model_dump()
    return load_app_settings()["skill_weights"]
