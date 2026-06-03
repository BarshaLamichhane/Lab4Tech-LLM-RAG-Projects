from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from backend.cv.cv_parser import extract_text_from_pdf
from backend.cv.cv_skill_extractor import extract_candidate_skill_profile
from backend.job_description.job_description_cleaner_mistral_api import (
    JobSkills,
    extract_job_skills,
    save_extracted_skills,
)
from backend.matching.skill_matching_engine import (
    DEFAULT_JOB_SKILLS_DIR,
    calculate_skill_match,
    get_saved_job_profile_by_role,
    load_saved_job_profiles,
    rank_candidate_against_saved_jobs,
)


def load_roles() -> list[str]:
    return sorted(load_saved_job_profiles(DEFAULT_JOB_SKILLS_DIR))


async def read_uploaded_text(uploaded_file: UploadFile | None) -> str:
    if uploaded_file is None:
        return ""

    file_bytes = await uploaded_file.read()
    filename = uploaded_file.filename or ""

    if uploaded_file.content_type == "application/pdf" or filename.lower().endswith(".pdf"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name

        try:
            return extract_text_from_pdf(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    return file_bytes.decode("utf-8", errors="ignore")


def extract_job_profile(job_description_text: str, save_job_profile: bool) -> tuple[dict[str, Any], Path | None]:
    if not job_description_text.strip():
        raise ValueError("job_description_text cannot be empty")

    extracted_job = extract_job_skills(job_description_text)
    saved_path = save_extracted_skills(extracted_job, DEFAULT_JOB_SKILLS_DIR) if save_job_profile else None
    return extracted_job.model_dump(), saved_path


def build_saved_job_match(
    cv_text: str,
    target_role: str,
    include_all_saved_jobs: bool = False,
) -> dict[str, Any]:
    if not cv_text.strip():
        raise ValueError("cv_text cannot be empty")
    if not target_role.strip():
        raise ValueError("target_role cannot be empty")

    saved_job_profiles = load_saved_job_profiles(DEFAULT_JOB_SKILLS_DIR)
    target_job_profile = get_saved_job_profile_by_role(target_role, DEFAULT_JOB_SKILLS_DIR)
    candidate_profile = extract_candidate_skill_profile(
        cv_text,
        job_profiles=list(saved_job_profiles.values()),
    )
    target_match = calculate_skill_match(candidate_profile, target_job_profile)

    result = {
        "candidate_profile": candidate_profile.model_dump(),
        "target_job_match": target_match.model_dump(),
        "target_job_profile": target_job_profile,
        "all_saved_job_matches": [],
    }

    if include_all_saved_jobs:
        result["all_saved_job_matches"] = [
            match_result.model_dump()
            for match_result in rank_candidate_against_saved_jobs(candidate_profile, DEFAULT_JOB_SKILLS_DIR)
        ]

    return result


def build_new_job_match(
    cv_text: str,
    job_description_text: str,
    save_new_job_profile: bool = True,
    include_all_saved_jobs: bool = False,
) -> dict[str, Any]:
    if not cv_text.strip():
        raise ValueError("cv_text cannot be empty")

    target_job_profile, _ = extract_job_profile(job_description_text, save_new_job_profile)
    saved_job_profiles = load_saved_job_profiles(DEFAULT_JOB_SKILLS_DIR)
    candidate_profile = extract_candidate_skill_profile(
        cv_text,
        job_profiles=list(saved_job_profiles.values()) + [target_job_profile],
    )
    target_match = calculate_skill_match(candidate_profile, target_job_profile)

    result = {
        "candidate_profile": candidate_profile.model_dump(),
        "target_job_match": target_match.model_dump(),
        "target_job_profile": target_job_profile,
        "all_saved_job_matches": [],
    }

    if include_all_saved_jobs:
        result["all_saved_job_matches"] = [
            match_result.model_dump()
            for match_result in rank_candidate_against_saved_jobs(candidate_profile, DEFAULT_JOB_SKILLS_DIR)
        ]

    return result


def model_to_dict(model: JobSkills) -> dict[str, Any]:
    return model.model_dump()
