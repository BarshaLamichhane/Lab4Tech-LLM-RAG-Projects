from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MatchSavedJobRequest(BaseModel):
    cv_text: str
    target_role: str
    include_all_saved_jobs: bool = False


class MatchNewJobRequest(BaseModel):
    cv_text: str
    job_description_text: str
    save_new_job_profile: bool = True
    include_all_saved_jobs: bool = False


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

