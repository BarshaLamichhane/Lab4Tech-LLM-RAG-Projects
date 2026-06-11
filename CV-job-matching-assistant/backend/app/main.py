from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.app.schemas import (
    AppSettings,
    ChangePasswordRequest,
    CreateUserRequest,
    ExtractJobSkillsRequest,
    ExtractJobSkillsResponse,
    InterviewSessionRequest,
    InterviewSessionResponse,
    LoginRequest,
    LoginResponse,
    MatchNewJobRequest,
    MatchResponse,
    MatchSavedJobRequest,
    UserResponse,
)
from backend.app.auth import (
    CurrentUser,
    authenticate,
    change_password,
    create_user,
    create_access_token,
    initialize_auth_database,
    require_user,
)
from backend.app.config import CONFIG
from backend.app.evaluation_audit_store import (
    initialize_evaluation_audit_database,
    save_evaluation_audit,
)
from backend.app.session_store import (
    initialize_session_database,
    load_interview_session,
    load_interview_sessions,
    load_user_sessions,
    save_interview_session,
    save_user_session,
)
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
    evaluate_answer_with_audit,
)
from backend.interview.preparation_interview import (
    generate_preparation_interview,
    regenerate_preparation_question,
)
from backend.interview.progress_dashboard import build_progress_dashboard
from backend.job_description.job_description_cleaner_mistral_api import MISTRAL_API_MODEL_NAME
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
    InterviewQuestion,
    LearningPathRequest,
    PreparationInterviewRequest,
    PreparationInterviewResponse,
    QuestionQualityReportRequest,
    RegeneratePreparationQuestionRequest,
)
from backend.cv.cv_skill_extractor import load_skill_categories as load_cv_skill_categories
from backend.matching.skill_matching_engine import load_skill_categories as load_matching_skill_categories


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_auth_database()
    initialize_session_database()
    initialize_evaluation_audit_database()
    yield


app = FastAPI(
    title="CV Job Matching Assistant API",
    docs_url="/docs" if CONFIG.api_docs_enabled else None,
    redoc_url="/redoc" if CONFIG.api_docs_enabled else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CONFIG.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=CONFIG.allowed_hosts)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def reject_cross_origin_cookie_writes(request: Request, call_next):
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("origin")
        uses_cookie = CONFIG.auth_cookie_name in request.cookies
        same_origin = str(request.base_url).rstrip("/")
        trusted_origins = {*CONFIG.cors_allowed_origins, same_origin}
        if uses_cookie and origin and origin not in trusted_origins:
            return Response(status_code=403, content="Cross-origin request rejected")
    return await call_next(request)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=LoginResponse)
def login_route(request: LoginRequest, response: Response, http_request: Request) -> LoginResponse:
    client_host = http_request.client.host if http_request.client else "unknown"
    user = authenticate(request.username, request.password, f"{client_host}:{request.username.lower()}")
    response.set_cookie(
        key=CONFIG.auth_cookie_name,
        value=create_access_token(user),
        httponly=True,
        secure=CONFIG.cookie_secure,
        samesite=CONFIG.cookie_samesite,
        max_age=CONFIG.access_token_minutes * 60,
        path="/",
    )
    return LoginResponse(username=user.username, role=user.role)


@app.post("/api/auth/logout", status_code=204)
def logout_route() -> Response:
    response = Response(status_code=204)
    response.delete_cookie(
        key=CONFIG.auth_cookie_name,
        secure=CONFIG.cookie_secure,
        samesite=CONFIG.cookie_samesite,
        path="/",
    )
    return response


@app.get("/api/auth/me")
def current_user_route(user: CurrentUser = Depends(require_user)) -> dict[str, str]:
    return {"username": user.username, "role": user.role}


@app.post("/api/auth/change-password", status_code=204)
def change_password_route(
    request: ChangePasswordRequest,
    user: CurrentUser = Depends(require_user),
) -> Response:
    try:
        change_password(user, request.current_password, request.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = Response(status_code=204)
    response.delete_cookie(
        key=CONFIG.auth_cookie_name,
        secure=CONFIG.cookie_secure,
        samesite=CONFIG.cookie_samesite,
        path="/",
    )
    return response


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


@app.post("/api/admin/users", response_model=UserResponse, status_code=201)
def create_admin_user(
    request: CreateUserRequest,
    user: CurrentUser = Depends(require_user),
) -> CurrentUser:
    _ensure_admin(user)
    try:
        return create_user(request.username, request.password, request.role)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/sessions")
def get_user_sessions(user: CurrentUser = Depends(require_user)) -> list[dict]:
    return load_user_sessions(user.username)


@app.get("/api/interview/sessions", response_model=list[InterviewSessionResponse])
def get_interview_sessions(user: CurrentUser = Depends(require_user)) -> list[dict]:
    return load_interview_sessions(user.username)


@app.get("/api/interview/progress")
def get_interview_progress(user: CurrentUser = Depends(require_user)) -> dict:
    return build_progress_dashboard(load_interview_sessions(user.username))


@app.get("/api/interview/sessions/{session_id}", response_model=InterviewSessionResponse)
def get_interview_session(
    session_id: str,
    user: CurrentUser = Depends(require_user),
) -> dict:
    try:
        return load_interview_session(user.username, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/interview/sessions", response_model=InterviewSessionResponse, status_code=201)
def create_interview_session(
    request: InterviewSessionRequest,
    user: CurrentUser = Depends(require_user),
) -> dict:
    return save_interview_session(
        username=user.username,
        title=request.title,
        payload=request.payload,
        status=request.status,
    )


@app.put("/api/interview/sessions/{session_id}", response_model=InterviewSessionResponse)
def update_interview_session(
    session_id: str,
    request: InterviewSessionRequest,
    user: CurrentUser = Depends(require_user),
) -> dict:
    try:
        return save_interview_session(
            username=user.username,
            title=request.title,
            payload=request.payload,
            status=request.status,
            session_id=session_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


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
        evaluation, prompt, raw_response = evaluate_answer_with_audit(
            question=request.question,
            answer=request.answer,
            context=request.context,
            interview_engine="mistral",
        )
        save_evaluation_audit(
            username=user.username,
            question_id=request.question.id,
            model=MISTRAL_API_MODEL_NAME,
            prompt=prompt,
            raw_response=raw_response,
            evaluation=evaluation.model_dump(),
        )
        return evaluation
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
            candidate_projects=request.candidate_projects,
            question_count=request.question_count,
            level=request.level,
            interview_type=request.interview_type,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/interview/preparation/regenerate", response_model=InterviewQuestion)
def regenerate_preparation_question_route(
    request: RegeneratePreparationQuestionRequest,
    user: CurrentUser = Depends(require_user),
) -> InterviewQuestion:
    try:
        return regenerate_preparation_question(
            role=request.role,
            selected_skills=request.selected_skills,
            candidate_projects=request.candidate_projects,
            level=request.level,
            interview_type=request.interview_type,
            question_id=request.question_id,
            existing_questions=[
                question for question in request.existing_questions if question.id != request.question_id
            ],
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/interview/questions/report", status_code=201)
def report_interview_question(
    request: QuestionQualityReportRequest,
    user: CurrentUser = Depends(require_user),
) -> dict[str, str]:
    report = save_user_session(
        user.username,
        "question_quality_report",
        request.question.question[:120],
        request.model_dump(),
    )
    return {"id": report["id"], "status": "reported"}


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
    if not CONFIG.code_execution_enabled:
        raise HTTPException(status_code=503, detail="Live code execution is disabled")
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
