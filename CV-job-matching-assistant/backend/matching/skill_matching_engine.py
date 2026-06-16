"""Compare a candidate skill profile against extracted job descriptions."""

from __future__ import annotations

import argparse
import json
import re
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field
from backend.job_description.job_profile_catalog import profile_display_name, profile_paths

try:
    from backend.cv.cv_parser import read_cv_text
    from backend.cv.cv_skill_extractor import (
        CandidateSkillProfile,
        extract_candidate_skill_profile,
        normalize_skill,
    )
except ModuleNotFoundError:
    from backend.cv.cv_parser import read_cv_text
    from backend.cv.cv_skill_extractor import (
        CandidateSkillProfile,
        extract_candidate_skill_profile,
        normalize_skill,
    )


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_JOB_SKILLS_DIR = PROJECT_ROOT / "data" / "extracted_skills_mistral-large-latest"
SKILL_CATEGORIES_PATH = PROJECT_ROOT / "data" / "taxonomies" / "skill_categories.json"

SKILL_WEIGHTS = {
    "strongly_required_skills": 3.0,
    "required_skills": 2.0,
    "tools_and_platforms": 1.5,
    "preferred_skills": 1.0,
    "soft_skills": 0.5,
}

SKILL_CATEGORY_LABELS = {
    "strongly_required_skills": "Strongly required",
    "required_skills": "Required",
    "tools_and_platforms": "Tools and platforms",
    "preferred_skills": "Preferred",
    "soft_skills": "Soft skills",
}


class SkillCategoryBreakdown(BaseModel):
    """Score contribution for one job-skill category."""

    category: str
    label: str
    weight: float
    matched_count: int = 0
    total_count: int = 0
    matched_weight: float = 0.0
    total_weight: float = 0.0
    contribution_percent: float = 0.0
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)


class SkillMatchResult(BaseModel):
    """Percentage match result for one candidate against one job profile."""

    target_role: str
    score: float
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    matched_strongly_required_skills: list[str] = Field(default_factory=list)
    missing_strongly_required_skills: list[str] = Field(default_factory=list)
    candidate_skills: list[str] = Field(default_factory=list)
    total_possible_weight: float = 0.0
    matched_weight: float = 0.0
    score_breakdown: list[SkillCategoryBreakdown] = Field(default_factory=list)


def normalize_for_matching(value: str) -> str:
    """Normalize a skill label into a lowercase comparable representation."""
    normalized = normalize_skill(value).lower()
    normalized = normalized.replace("&", "and")
    normalized = re.sub(r"[^a-z0-9+#.]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


@lru_cache(maxsize=1)
def load_skill_categories(path: Path = SKILL_CATEGORIES_PATH) -> dict:
    """Load shared skill taxonomy settings used by skill matching."""
    if not path.exists():
        return {}

    with path.open(encoding="utf-8") as file:
        return json.load(file)


def load_broad_skill_aliases() -> dict[str, list[str]]:
    """Load broad-skill alias groups from the taxonomy file."""
    aliases = load_skill_categories().get("broad_skill_aliases", {})
    if not isinstance(aliases, dict):
        return {}

    normalized_aliases = {}
    for broad_skill, broad_aliases in aliases.items():
        if not isinstance(broad_skill, str) or not isinstance(broad_aliases, list):
            continue

        normalized_aliases[normalize_for_matching(broad_skill)] = [
            normalize_for_matching(alias)
            for alias in broad_aliases
            if isinstance(alias, str) and alias.strip()
        ]

    return normalized_aliases


def load_skill_aliases_for_matching() -> dict[str, str]:
    """Load alias-to-canonical mappings normalized for match comparison."""
    aliases = load_skill_categories().get("skill_aliases", {})
    if not isinstance(aliases, dict):
        return {}
    return {
        normalize_for_matching(alias): normalize_for_matching(canonical)
        for alias, canonical in aliases.items()
        if isinstance(alias, str) and isinstance(canonical, str) and alias.strip() and canonical.strip()
    }


def load_saved_job_profiles(data_dir: Path = DEFAULT_JOB_SKILLS_DIR) -> dict[str, dict]:
    """Load all saved extracted job-description profiles from disk."""
    job_profiles = {}

    if not data_dir.exists():
        return job_profiles

    for file_path in profile_paths(data_dir):
        with file_path.open(encoding="utf-8") as file:
            job_profile = json.load(file)

        role = job_profile.get("role") or file_path.stem.replace("_skills", "").replace("_", " ").title()
        display_name = profile_display_name(job_profile)
        job_profiles[display_name if display_name not in job_profiles else f"{display_name} ({file_path.stem})"] = job_profile

    return job_profiles


def _skill_from_strongly_required_item(item: str | dict) -> str:
    """Read a skill name from either a plain string or evidence-backed skill object."""
    if isinstance(item, dict):
        return item.get("skill", "")

    return item


def get_weighted_job_skills(job_profile: dict, skill_weights: dict[str, float] | None = None) -> dict[str, float]:
    """Flatten a job profile into unique skill names with their highest category weight."""
    weighted_skills = {}
    weights = skill_weights or SKILL_WEIGHTS

    for item in job_profile.get("strongly_required_skills", []):
        skill = _skill_from_strongly_required_item(item)
        _add_weighted_skill(weighted_skills, skill, weights["strongly_required_skills"])

    for field_name, weight in weights.items():
        if field_name == "strongly_required_skills":
            continue

        for skill in job_profile.get(field_name, []):
            _add_weighted_skill(weighted_skills, skill, weight)

    return weighted_skills


def get_category_skill_breakdown(
    job_profile: dict,
    candidate_skills: list[str],
    skill_weights: dict[str, float] | None = None,
) -> list[SkillCategoryBreakdown]:
    """Build score explanation rows for each weighted skill category."""
    weights = skill_weights or SKILL_WEIGHTS
    weighted_job_skills = get_weighted_job_skills(job_profile, skill_weights=weights)
    total_possible_weight = sum(weighted_job_skills.values())
    assigned_skills = set()
    breakdown = []

    for field_name, weight in weights.items():
        category_skills = []
        for skill in _job_skills_for_category(job_profile, field_name):
            if skill in assigned_skills or weighted_job_skills.get(skill) != weight:
                continue
            category_skills.append(skill)
            assigned_skills.add(skill)

        matched_skills = []
        missing_skills = []

        for skill in category_skills:
            if _find_matching_candidate_skill(skill, candidate_skills):
                matched_skills.append(skill)
            else:
                missing_skills.append(skill)

        matched_weight = len(matched_skills) * weight
        total_weight = len(category_skills) * weight
        contribution_percent = 0.0
        if total_possible_weight:
            contribution_percent = round((matched_weight / total_possible_weight) * 100, 2)

        breakdown.append(
            SkillCategoryBreakdown(
                category=field_name,
                label=SKILL_CATEGORY_LABELS.get(field_name, field_name.replace("_", " ").title()),
                weight=round(weight, 2),
                matched_count=len(matched_skills),
                total_count=len(category_skills),
                matched_weight=round(matched_weight, 2),
                total_weight=round(total_weight, 2),
                contribution_percent=contribution_percent,
                matched_skills=sorted(matched_skills, key=str.lower),
                missing_skills=sorted(missing_skills, key=str.lower),
            )
        )

    return breakdown


def _job_skills_for_category(job_profile: dict, field_name: str) -> list[str]:
    if field_name == "strongly_required_skills":
        return [
            normalize_skill(_skill_from_strongly_required_item(item))
            for item in job_profile.get(field_name, [])
            if _skill_from_strongly_required_item(item)
        ]

    return [
        normalize_skill(skill)
        for skill in job_profile.get(field_name, [])
        if isinstance(skill, str) and skill.strip()
    ]


def _add_weighted_skill(weighted_skills: dict[str, float], skill: str, weight: float) -> None:
    """Add a skill to the weighted skill map, keeping the strongest weight for duplicates."""
    normalized_skill = normalize_skill(skill)
    if not normalized_skill:
        return

    existing_weight = weighted_skills.get(normalized_skill, 0.0)
    weighted_skills[normalized_skill] = max(existing_weight, weight)


def skills_match(candidate_skill: str, job_skill: str) -> bool:
    """Return True when a candidate skill should count as matching a job skill."""
    candidate = normalize_for_matching(candidate_skill)
    job = normalize_for_matching(job_skill)
    skill_aliases = load_skill_aliases_for_matching()
    candidate = skill_aliases.get(candidate, candidate)
    job = skill_aliases.get(job, job)

    if not candidate or not job:
        return False

    if candidate == job:
        return True

    if len(candidate) >= 4 and candidate in job:
        return True

    if len(job) >= 4 and job in candidate:
        return True

    for broad_skill, aliases in load_broad_skill_aliases().items():
        normalized_aliases = set(aliases)
        if job == broad_skill and candidate in normalized_aliases:
            return True

        if candidate == broad_skill and job in normalized_aliases:
            return True

    return False


def _find_matching_candidate_skill(job_skill: str, candidate_skills: list[str]) -> str | None:
    """Find the first candidate skill that matches one job skill."""
    for candidate_skill in candidate_skills:
        if skills_match(candidate_skill, job_skill):
            return candidate_skill

    return None


def calculate_skill_match(
    candidate_profile: CandidateSkillProfile | dict,
    job_profile: dict,
    skill_weights: dict[str, float] | None = None,
) -> SkillMatchResult:
    """Calculate the weighted percentage match between a candidate and one job profile."""
    candidate_skills = candidate_profile.skills if isinstance(candidate_profile, CandidateSkillProfile) else candidate_profile.get("skills", [])
    candidate_skills = [normalize_skill(skill) for skill in candidate_skills if skill]
    weighted_job_skills = get_weighted_job_skills(job_profile, skill_weights=skill_weights)
    score_breakdown = get_category_skill_breakdown(
        job_profile,
        candidate_skills,
        skill_weights=skill_weights,
    )

    matched_skills = []
    missing_skills = []
    matched_weight = 0.0
    total_possible_weight = sum(weighted_job_skills.values())

    for job_skill, weight in weighted_job_skills.items():
        matching_candidate_skill = _find_matching_candidate_skill(job_skill, candidate_skills)
        if matching_candidate_skill:
            matched_skills.append(job_skill)
            matched_weight += weight
        else:
            missing_skills.append(job_skill)

    strongly_required_skills = [
        _skill_from_strongly_required_item(item)
        for item in job_profile.get("strongly_required_skills", [])
    ]
    missing_strongly_required_skills = [
        skill
        for skill in strongly_required_skills
        if not _find_matching_candidate_skill(skill, candidate_skills)
    ]
    matched_strongly_required_skills = [
        skill
        for skill in strongly_required_skills
        if _find_matching_candidate_skill(skill, candidate_skills)
    ]

    score = 0.0
    if total_possible_weight:
        score = round((matched_weight / total_possible_weight) * 100, 2)

    return SkillMatchResult(
        target_role=job_profile.get("role", "Unknown role"),
        score=score,
        matched_skills=sorted(matched_skills, key=str.lower),
        missing_skills=sorted(missing_skills, key=str.lower),
        matched_strongly_required_skills=sorted(matched_strongly_required_skills, key=str.lower),
        missing_strongly_required_skills=sorted(missing_strongly_required_skills, key=str.lower),
        candidate_skills=sorted(candidate_skills, key=str.lower),
        total_possible_weight=round(total_possible_weight, 2),
        matched_weight=round(matched_weight, 2),
        score_breakdown=score_breakdown,
    )


def rank_candidate_against_saved_jobs(
    candidate_profile: CandidateSkillProfile | dict,
    data_dir: Path = DEFAULT_JOB_SKILLS_DIR,
    skill_weights: dict[str, float] | None = None,
) -> list[SkillMatchResult]:
    """Calculate percentage match against every saved extracted job profile."""
    job_profiles = load_saved_job_profiles(data_dir)
    results = [
        calculate_skill_match(candidate_profile, job_profile, skill_weights=skill_weights)
        for job_profile in job_profiles.values()
    ]

    return sorted(results, key=lambda result: result.score, reverse=True)


def get_saved_job_profile_by_role(
    role: str,
    data_dir: Path = DEFAULT_JOB_SKILLS_DIR,
) -> dict:
    """Find one saved extracted job profile by role name."""
    normalized_target_role = normalize_for_matching(role)
    job_profiles = load_saved_job_profiles(data_dir)

    for saved_role, job_profile in job_profiles.items():
        if normalize_for_matching(saved_role) == normalized_target_role:
            return job_profile
        if normalize_for_matching(job_profile.get("role", "")) == normalized_target_role:
            return job_profile

    available_roles = ", ".join(sorted(job_profiles))
    raise ValueError(f"Saved job role '{role}' not found. Available roles: {available_roles}")


def compare_cv_text_with_saved_job(
    cv_text: str,
    target_role: str,
    saved_jobs_dir: Path = DEFAULT_JOB_SKILLS_DIR,
) -> dict:
    """Compare CV text with one saved job role and also return matches for all saved jobs."""
    target_job_profile = get_saved_job_profile_by_role(target_role, saved_jobs_dir)
    return compare_cv_text_with_job_profile(
        cv_text=cv_text,
        job_profile=target_job_profile,
        saved_jobs_dir=saved_jobs_dir,
    )


def compare_cv_text_with_job_profile(
    cv_text: str,
    job_profile: dict,
    saved_jobs_dir: Path = DEFAULT_JOB_SKILLS_DIR,
) -> dict:
    """Extract CV skills, compare with one job profile, and rank against saved jobs."""
    saved_job_profiles = list(load_saved_job_profiles(saved_jobs_dir).values())
    candidate_profile = extract_candidate_skill_profile(
        cv_text,
        job_profiles=saved_job_profiles + [job_profile],
    )

    return {
        "candidate_profile": candidate_profile.model_dump(),
        "target_job_match": calculate_skill_match(candidate_profile, job_profile).model_dump(),
        "all_saved_job_matches": [
            result.model_dump()
            for result in rank_candidate_against_saved_jobs(candidate_profile, saved_jobs_dir)
        ],
    }


def load_job_profile_file(job_profile_file: str | Path) -> dict:
    """Load one extracted job profile JSON file from disk."""
    with Path(job_profile_file).open(encoding="utf-8") as file:
        return json.load(file)


def save_match_result(result: dict, output_path: str | Path) -> Path:
    """Save a CV/job match result as JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=4), encoding="utf-8")
    return path


def main() -> None:
    """Run skill matching as an individual command-line module."""
    parser = argparse.ArgumentParser(description="Match a CV against saved or provided job profiles.")
    parser.add_argument("cv_file", help="Path to a PDF or TXT CV file.")
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--target-role", help="Role name from saved extracted job profiles.")
    target_group.add_argument("--job-profile-file", help="Path to one extracted job profile JSON file.")
    parser.add_argument(
        "--job-skills-dir",
        type=Path,
        default=DEFAULT_JOB_SKILLS_DIR,
        help="Directory containing saved extracted job profile JSON files.",
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Also calculate matches against all saved jobs.",
    )
    parser.add_argument("--output", help="Optional path to save match result JSON.")
    args = parser.parse_args()

    cv_text = read_cv_text(args.cv_file)

    if args.target_role:
        result = compare_cv_text_with_saved_job(
            cv_text=cv_text,
            target_role=args.target_role,
            saved_jobs_dir=args.job_skills_dir,
        )
        if not args.show_all:
            result.pop("all_saved_job_matches", None)
    else:
        job_profile = load_job_profile_file(args.job_profile_file)
        result = compare_cv_text_with_job_profile(
            cv_text=cv_text,
            job_profile=job_profile,
            saved_jobs_dir=args.job_skills_dir,
        )
        if not args.show_all:
            result.pop("all_saved_job_matches", None)

    if args.output:
        save_match_result(result, args.output)
    else:
        print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
