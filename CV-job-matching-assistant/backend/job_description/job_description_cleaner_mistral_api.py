"""Extract structured job skills from job descriptions using the Mistral API."""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from string import Template
from typing import Any

import yaml
from dotenv import load_dotenv
from mistralai.client import Mistral
from pydantic import BaseModel, Field, ValidationError
from backend.job_description.job_profile_catalog import update_profile_catalog

try:
    from backend.cv.cv_skill_extractor import (
        load_generic_skill_terms,
        load_skill_aliases,
        normalize_skill,
        normalize_text,
    )
except ModuleNotFoundError:
    from backend.cv.cv_skill_extractor import (
        load_generic_skill_terms,
        load_skill_aliases,
        normalize_skill,
        normalize_text,
    )


logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
PROMPTS_DIR = PROJECT_ROOT / "prompts"

load_dotenv(PROJECT_ROOT / ".env")

DEFAULT_MISTRAL_MODEL = "mistral-large-latest"
MISTRAL_API_MODEL_NAME = os.getenv("MISTRAL_API_MODEL_NAME", DEFAULT_MISTRAL_MODEL)
MISTRAL_API_TIMEOUT_MS = int(os.getenv("MISTRAL_API_TIMEOUT_MS", "120000"))

OUTPUT_JOB_DESCRIPTION_SKILLS_DIR = DATA_DIR / f"extracted_skills_{MISTRAL_API_MODEL_NAME}"
SKILL_CATEGORIES_PATH = DATA_DIR / "taxonomies" / "skill_categories.json"
JOB_DESCRIPTION_PROMPTS_PATH = PROMPTS_DIR / "job_description_data_extractor.yml"

MISTRAL_JOB_DESCRIPTION_PROMPT_NAME = "mistral_api_job_description_extractor"
DEFAULT_PROGRAMMING_LANGUAGES = {"python", "java", "javascript", "typescript", "sql"}


class SkillEvidence(BaseModel):
    skill: str
    verbatim: str


class JobSkills(BaseModel):
    role: str = ""
    company_name: str = ""
    company_context: str = ""
    industry_domain: str = ""
    business_problem: str = ""
    strongly_required_skills: list[SkillEvidence] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    tools_and_platforms: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)


def get_mistral_client(api_key: str | None = None) -> Mistral:
    resolved_api_key = api_key or os.getenv("MISTRAL_API_KEY")
    if not resolved_api_key:
        raise ValueError("MISTRAL_API_KEY not found in environment or .env file")

    return Mistral(api_key=resolved_api_key, timeout_ms=MISTRAL_API_TIMEOUT_MS)


def _load_json_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.warning("Could not parse JSON file %s: %s", path, exc)
        return {}


def load_programming_languages(path: Path = SKILL_CATEGORIES_PATH) -> set[str]:
    categories = _load_json_file(path)
    languages = categories.get("programming_languages", [])

    if not isinstance(languages, list):
        return DEFAULT_PROGRAMMING_LANGUAGES

    normalized_languages = {
        language.strip().lower()
        for language in languages
        if isinstance(language, str) and language.strip()
    }

    return normalized_languages or DEFAULT_PROGRAMMING_LANGUAGES


def load_job_description_prompt(
    prompt_name: str,
    job_description: str,
    prompt_path: Path = JOB_DESCRIPTION_PROMPTS_PATH,
) -> str:
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    prompts = yaml.safe_load(prompt_path.read_text(encoding="utf-8")) or {}
    if prompt_name not in prompts:
        raise KeyError(f"Prompt '{prompt_name}' not found in {prompt_path}")

    return Template(prompts[prompt_name]).substitute(job_description=job_description)


def _is_experience_duration(skill_evidence: SkillEvidence) -> bool:
    text = f"{skill_evidence.skill} {skill_evidence.verbatim}".lower()
    has_years = re.search(r"\b\d+\+?\s*years?\b", text) is not None
    return has_years and "experience" in text


def _extract_skill_from_experience_duration(text: str) -> str | None:
    match = re.search(r"\b(?:with|in)\s+([^,(]+)", text)
    if not match:
        return None

    skill = match.group(1).strip()
    return skill or None


def _append_unique(values: list[str], value: str) -> None:
    normalized_value = normalize_skill(value)
    if normalized_value and normalized_value.lower() not in {existing.lower() for existing in values}:
        values.append(normalized_value)


def _unique_clean_strings(values: list[str]) -> list[str]:
    cleaned_values: list[str] = []
    for value in values:
        if isinstance(value, str):
            _append_unique(cleaned_values, value)

    return cleaned_values


def _remove_strongly_required_duplicates(
    values: list[str],
    strongly_required_skills: list[SkillEvidence],
) -> list[str]:
    strongly_required_names = {
        normalize_text(skill.skill)
        for skill in strongly_required_skills
        if skill.skill
    }
    return [value for value in values if normalize_text(value) not in strongly_required_names]


def _normalize_job_skill(value: str) -> str:
    """Normalize one job-skill label and canonicalize known taxonomy aliases."""
    normalized_value = normalize_skill(value)
    if not normalized_value:
        return ""

    return load_skill_aliases().get(normalize_text(normalized_value), normalized_value)


def _is_generic_skill(value: str) -> bool:
    return normalize_text(value) in load_generic_skill_terms()


def _normalize_required_skill(value: str) -> str:
    normalized_value = _normalize_job_skill(value)
    value_lower = normalized_value.lower()

    if value_lower == "python development":
        return "Python"

    if re.search(
        r"\b(data ingestion|data processing|data labeling|data curation|data annotation|data preparation)\b",
        value_lower,
    ):
        return "Data preparation and labeling"

    if re.search(r"\b(training|fine-tuning|testing|deploying)\s+machine learning models?\b", value_lower):
        return "Model training and deployment"

    if re.search(r"\bmachine learning model[- ]?(training|deployment|testing|fine-tuning)\b", value_lower):
        return "Model training and deployment"

    if "secure storage" in value_lower and "model training" in value_lower:
        return "ML data management"

    if value_lower.startswith("cloud platforms"):
        return "Cloud platforms"

    return normalized_value


def _remove_strongly_required_covered_details(
    values: list[str],
    strongly_required_skills: list[SkillEvidence],
) -> list[str]:
    strongly_required_quotes = [
        skill.verbatim.lower()
        for skill in strongly_required_skills
        if skill.verbatim
    ]

    return [
        value
        for value in values
        if not any(
            value.lower() in quote
            or value.lower().removeprefix("image ") in quote
            for quote in strongly_required_quotes
        )
    ]


def _is_soft_or_workstyle_skill(value: str) -> bool:
    value_lower = value.lower()
    soft_markers = [
        "ownership",
        "collaboration",
        "collaborative",
        "communication",
        "distributed teams",
        "work independently",
        "teamwork",
        "problem-solving",
        "problem solving",
    ]
    return any(marker in value_lower for marker in soft_markers)


def _clean_required_skills(
    values: list[str],
    strongly_required_skills: list[SkillEvidence],
) -> list[str]:
    normalized_values = [_normalize_required_skill(value) for value in values]
    unique_values = _unique_clean_strings(normalized_values)
    unique_values = [
        value
        for value in unique_values
        if not _is_soft_or_workstyle_skill(value) and not _is_generic_skill(value)
    ]
    unique_values = _remove_strongly_required_duplicates(unique_values, strongly_required_skills)
    return _remove_strongly_required_covered_details(unique_values, strongly_required_skills)


def _is_years_duration_or_seniority(value: str) -> bool:
    value_lower = value.lower()
    return (
        re.search(r"\b\d+\+?\s*(years?|months?)\b", value_lower) is not None
        or any(term in value_lower for term in ["senior", "junior", "mid-level", "lead"])
    )


def _clean_experience(
    values: list[str],
    strongly_required_skills: list[SkillEvidence],
) -> list[str]:
    strongly_required_quotes = [
        skill.verbatim.lower()
        for skill in strongly_required_skills
        if skill.verbatim
    ]
    cleaned_experience: list[str] = []

    for value in _unique_clean_strings(values):
        value_lower = value.lower()
        if not _is_years_duration_or_seniority(value):
            continue

        duplicates_strong_requirement = any(
            value_lower in quote or quote in value_lower
            for quote in strongly_required_quotes
        )

        if not duplicates_strong_requirement:
            cleaned_experience.append(value)

    return cleaned_experience


def _clean_tools_and_platforms(values: list[str]) -> list[str]:
    programming_languages = load_programming_languages()
    return [
        value
        for value in _unique_clean_strings(_normalize_job_skill(value) for value in values)
        if value.lower() not in programming_languages and not _is_generic_skill(value)
    ]


def _clean_skill_list(values: list[str]) -> list[str]:
    return [
        value
        for value in _unique_clean_strings(_normalize_job_skill(value) for value in values)
        if value and not _is_generic_skill(value)
    ]


def _clean_strongly_required_skills(values: list[SkillEvidence]) -> list[SkillEvidence]:
    cleaned_values: list[SkillEvidence] = []
    seen_skills: set[str] = set()

    for skill_evidence in values:
        normalized_skill = _normalize_job_skill(skill_evidence.skill)
        if not normalized_skill or _is_generic_skill(normalized_skill):
            continue

        skill_key = normalize_text(normalized_skill)
        if skill_key in seen_skills:
            continue

        cleaned_values.append(
            SkillEvidence(
                skill=normalized_skill,
                verbatim=normalize_skill(skill_evidence.verbatim),
            )
        )
        seen_skills.add(skill_key)

    return cleaned_values


def clean_job_skills(data: JobSkills) -> JobSkills:
    cleaned_strongly_required_skills: list[SkillEvidence] = []

    for skill_evidence in data.strongly_required_skills:
        if _is_experience_duration(skill_evidence):
            _append_unique(data.experience, skill_evidence.verbatim)

            extracted_skill = _extract_skill_from_experience_duration(skill_evidence.verbatim)
            if extracted_skill:
                _append_unique(data.required_skills, extracted_skill)

            continue

        cleaned_strongly_required_skills.append(skill_evidence)

    data.role = normalize_skill(data.role)
    data.company_name = normalize_skill(data.company_name)
    data.company_context = normalize_skill(data.company_context)
    data.industry_domain = normalize_skill(data.industry_domain)
    data.business_problem = normalize_skill(data.business_problem)
    data.strongly_required_skills = _clean_strongly_required_skills(cleaned_strongly_required_skills)
    data.required_skills = _clean_required_skills(data.required_skills, data.strongly_required_skills)
    data.preferred_skills = _clean_skill_list(data.preferred_skills)
    data.soft_skills = _clean_skill_list(data.soft_skills)
    data.tools_and_platforms = _clean_tools_and_platforms(data.tools_and_platforms)
    data.experience = _clean_experience(data.experience, data.strongly_required_skills)
    data.responsibilities = _unique_clean_strings(data.responsibilities)
    return data


def _parse_job_skills_response(raw_output: str) -> JobSkills:
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Mistral returned invalid JSON: {exc}") from exc

    try:
        return clean_job_skills(JobSkills(**data))
    except ValidationError as exc:
        raise ValueError(f"Mistral JSON did not match JobSkills schema: {exc}") from exc


def extract_job_skills(
    job_description: str,
    client: Mistral | None = None,
    model_name: str = MISTRAL_API_MODEL_NAME,
) -> JobSkills:
    if not job_description.strip():
        raise ValueError("job_description cannot be empty")

    start_time = time.perf_counter()
    mistral_client = client or get_mistral_client()
    prompt = load_job_description_prompt(
        MISTRAL_JOB_DESCRIPTION_PROMPT_NAME,
        job_description,
    )

    response = mistral_client.chat.complete(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": "You extract structured JSON from job descriptions.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    raw_output = response.choices[0].message.content
    extracted_skills = _parse_job_skills_response(raw_output)
    logger.info(
        "Mistral API job skill extraction completed in %.2f seconds",
        time.perf_counter() - start_time,
    )
    return extracted_skills


def _slugify(value: str, fallback: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or fallback


def save_extracted_skills(
    data: JobSkills,
    output_dir: Path = OUTPUT_JOB_DESCRIPTION_SKILLS_DIR,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    year = datetime.now(UTC).year
    role_slug = _slugify(data.role, "unknown_role")
    company_slug = _slugify(data.company_name, "unknown_company")
    output_path = output_dir / f"{role_slug}_{company_slug}_{year}.json"

    output_path.write_text(
        data.model_dump_json(indent=4),
        encoding="utf-8",
    )
    update_profile_catalog(output_dir, data.model_dump(), output_path.name)
    logger.info("Saved extracted job skills to %s", output_path)
    return output_path


def extract_job_skills_from_file(
    input_path: str | Path,
    save_output: bool = False,
    output_dir: Path = OUTPUT_JOB_DESCRIPTION_SKILLS_DIR,
) -> JobSkills:
    """Extract structured skills from a job-description text file."""
    job_description = Path(input_path).read_text(encoding="utf-8")
    extracted_skills = extract_job_skills(job_description)

    if save_output:
        save_extracted_skills(extracted_skills, output_dir)

    return extracted_skills


def main() -> None:
    """Run job-description extraction as an individual command-line module."""
    parser = argparse.ArgumentParser(description="Extract structured job skills using the Mistral API.")
    parser.add_argument("job_description_file", help="Path to a TXT job-description file.")
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save the extracted job profile JSON to the output directory.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_JOB_DESCRIPTION_SKILLS_DIR,
        help="Directory where extracted job profile JSON should be saved.",
    )
    args = parser.parse_args()

    extracted_skills = extract_job_skills_from_file(
        input_path=args.job_description_file,
        save_output=args.save,
        output_dir=args.output_dir,
    )
    print(extracted_skills.model_dump_json(indent=4))


__all__ = [
    "JobSkills",
    "SkillEvidence",
    "clean_job_skills",
    "extract_job_skills",
    "get_mistral_client",
    "extract_job_skills_from_file",
    "load_job_description_prompt",
    "load_programming_languages",
    "save_extracted_skills",
]


if __name__ == "__main__":
    main()
