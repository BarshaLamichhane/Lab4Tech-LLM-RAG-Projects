from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app.schemas import JobDescriptionEvaluationDatasetRequest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVALUATION_DIR = PROJECT_ROOT / "evaluation"
JOB_DESCRIPTION_DIR = EVALUATION_DIR / "job_descriptions"
EXPECTED_JOB_SKILLS_PATH = EVALUATION_DIR / "expected_job_skills.json"


def save_job_description_evaluation_case(
    request: JobDescriptionEvaluationDatasetRequest,
) -> dict[str, Any]:
    JOB_DESCRIPTION_DIR.mkdir(parents=True, exist_ok=True)
    EXPECTED_JOB_SKILLS_PATH.parent.mkdir(parents=True, exist_ok=True)

    filename = _json_filename(request.filename or f"{request.role}_{request.company_name or 'unknown'}")

    job_description_path = JOB_DESCRIPTION_DIR / filename
    job_description_path.write_text(
        json.dumps(_job_description_payload(request), indent=2),
        encoding="utf-8",
    )

    expected_payload = _load_expected_payload()
    case_id = filename.removesuffix(".json")
    case = {
        "case_id": case_id,
        "job_description_file": f"job_descriptions/{filename}",
        "saved_profile_file": request.saved_profile_file.strip(),
        "expected_role": request.role.strip(),
        "expected_company": request.company_name.strip(),
        "expected_company_context": request.company_context.strip(),
        "expected_job_skills": {
            "strongly_required_skills": _clean_list(request.strongly_required_skills),
            "required_skills": _clean_list(request.required_skills),
            "preferred_skills": _clean_list(request.preferred_skills),
            "soft_skills": _clean_list(request.soft_skills),
            "tools_and_platforms": _clean_list(request.tools_and_platforms),
        },
    }
    expected_payload["cases"] = [
        existing_case
        for existing_case in expected_payload.get("cases", [])
        if existing_case.get("case_id") != case_id
    ]
    expected_payload["cases"].append(case)
    expected_payload["cases"].sort(key=lambda item: str(item.get("case_id", "")))
    EXPECTED_JOB_SKILLS_PATH.write_text(json.dumps(expected_payload, indent=2), encoding="utf-8")

    return {
        "case_id": case_id,
        "job_description_file": str(job_description_path.relative_to(PROJECT_ROOT)),
        "expected_job_skills_file": str(EXPECTED_JOB_SKILLS_PATH.relative_to(PROJECT_ROOT)),
        "updated_at": datetime.now(UTC).isoformat(),
    }


def _job_description_payload(request: JobDescriptionEvaluationDatasetRequest) -> dict[str, Any]:
    return {
        "role": request.role.strip(),
        "company_name": request.company_name.strip(),
        "company_context": request.company_context.strip(),
        "industry_domain": request.industry_domain.strip(),
        "business_problem": request.business_problem.strip(),
        "strongly_required_skills": _clean_list(request.strongly_required_skills),
        "required_skills": _clean_list(request.required_skills),
        "preferred_skills": _clean_list(request.preferred_skills),
        "soft_skills": _clean_list(request.soft_skills),
        "tools_and_platforms": _clean_list(request.tools_and_platforms),
        "experience": _clean_list(request.experience),
        "responsibilities": _clean_list(request.responsibilities),
    }


def _load_expected_payload() -> dict[str, Any]:
    if EXPECTED_JOB_SKILLS_PATH.exists():
        try:
            payload = json.loads(EXPECTED_JOB_SKILLS_PATH.read_text(encoding="utf-8"))
            if isinstance(payload.get("cases"), list):
                return payload
        except json.JSONDecodeError:
            pass

    return {
        "version": "0.1",
        "description": "Gold labels for evaluating job-description skill extraction only.",
        "evaluation_notes": [
            "This file evaluates saved Mistral-extracted job profile JSON files against manually labeled expected job skills.",
            "It does not evaluate CV extraction or CV-job matching.",
            "If a saved_profile_file is empty, the evaluator tries to find a saved profile by role and company.",
        ],
        "cases": [],
    }


def _safe_filename(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "_", value.strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("._-")
    if not normalized:
        return "job_description_case"
    return normalized


def _json_filename(value: str) -> str:
    filename = _safe_filename(value)
    stem = filename.removesuffix(".txt").removesuffix(".json")
    return f"{stem}.json"


def _clean_list(values: list[str]) -> list[str]:
    cleaned = []
    seen = set()
    for value in values:
        if not isinstance(value, str):
            continue
        normalized = re.sub(r"\s+", " ", value.strip())
        key = normalized.casefold()
        if normalized and key not in seen:
            cleaned.append(normalized)
            seen.add(key)
    return cleaned
