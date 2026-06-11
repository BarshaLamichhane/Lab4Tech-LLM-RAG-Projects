from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class SkillWeights(BaseModel):
    strongly_required_skills: float = Field(default=3.0, ge=0)
    required_skills: float = Field(default=2.0, ge=0)
    tools_and_platforms: float = Field(default=1.5, ge=0)
    preferred_skills: float = Field(default=1.0, ge=0)
    soft_skills: float = Field(default=0.5, ge=0)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    username: str
    role: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=12)
    role: Literal["admin", "user"] = "user"


class UserResponse(BaseModel):
    username: str
    role: str


class AppSettings(BaseModel):
    skill_weights: SkillWeights
    skill_aliases: dict[str, str] = Field(default_factory=dict)
    broad_skill_aliases: dict[str, list[str]] = Field(default_factory=dict)


class MatchSavedJobRequest(BaseModel):
    cv_text: str
    target_role: str
    include_all_saved_jobs: bool = False
    skill_weights: SkillWeights | None = None


class MatchNewJobRequest(BaseModel):
    cv_text: str
    job_description_text: str
    save_new_job_profile: bool = True
    include_all_saved_jobs: bool = False
    skill_weights: SkillWeights | None = None


class ExtractJobSkillsRequest(BaseModel):
    job_description_text: str
    save_job_profile: bool = True


class MatchResponse(BaseModel):
    candidate_profile: dict[str, Any]
    target_job_match: dict[str, Any]
    target_job_profile: dict[str, Any] | None = None
    all_saved_job_matches: list[dict[str, Any]] = Field(default_factory=list)


class ExtractJobSkillsResponse(BaseModel):
    job_profile: dict[str, Any]
    saved_path: str | None = None


class InterviewSessionRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    status: Literal["in_progress", "paused", "completed"] = "in_progress"
    payload: dict[str, Any]


class InterviewSessionResponse(InterviewSessionRequest):
    id: str
    username: str
    session_type: str
    created_at: str
    updated_at: str
