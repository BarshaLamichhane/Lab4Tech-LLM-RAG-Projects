"""Extract candidate skills from CV text using a controlled skill vocabulary."""

from __future__ import annotations

import argparse
import json
import re
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field

try:
    from src.cv.cv_analyzer import analyze_cv
    from src.cv.cv_parser import read_cv_text
except ModuleNotFoundError:
    from cv.cv_analyzer import analyze_cv
    from cv.cv_parser import read_cv_text


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_JOB_SKILLS_DIR = PROJECT_ROOT / "data" / "extracted_skills_mistral-large-latest"
ESCO_TERMS_PATH = PROJECT_ROOT / "data" / "taxonomies" / "esco" / "skills_en_terms.txt"
SKILL_CATEGORIES_PATH = PROJECT_ROOT / "data" / "taxonomies" / "skill_categories.json"


class CandidateSkillProfile(BaseModel):
    """Structured skill profile extracted from a candidate CV."""

    email: str | None = None
    estimated_experience_years: int = 0
    skills: list[str] = Field(default_factory=list)


def normalize_text(value: str) -> str:
    """Normalize text so phrase matching is consistent across CVs and job profiles."""
    return re.sub(r"\s+", " ", value.lower()).strip()


def normalize_skill(value: str) -> str:
    """Normalize one skill label while preserving readable punctuation like C++ and C#."""
    cleaned_value = re.sub(r"\s+", " ", value.strip())
    return cleaned_value.rstrip(".")


@lru_cache(maxsize=1)
def load_skill_categories(path: Path = SKILL_CATEGORIES_PATH) -> dict:
    """Load shared skill taxonomy settings used by extraction and normalization."""
    if not path.exists():
        return {}

    with path.open(encoding="utf-8") as file:
        return json.load(file)


def load_skill_aliases() -> dict[str, str]:
    """Load alias-to-canonical skill mappings from the taxonomy file."""
    aliases = load_skill_categories().get("skill_aliases", {})
    if not isinstance(aliases, dict):
        return {}

    return {
        normalize_text(alias): normalize_skill(canonical_skill)
        for alias, canonical_skill in aliases.items()
        if isinstance(alias, str) and isinstance(canonical_skill, str)
    }


def load_generic_skill_terms() -> set[str]:
    """Load overly generic terms that should not be returned as standalone skills."""
    terms = load_skill_categories().get("generic_skill_terms", [])
    if not isinstance(terms, list):
        return set()

    return {
        normalize_text(term)
        for term in terms
        if isinstance(term, str) and term.strip()
    }


def load_job_profiles(data_dir: Path = DEFAULT_JOB_SKILLS_DIR) -> list[dict]:
    """Load extracted job-skill JSON files from the saved Mistral output directory."""
    if not data_dir.exists():
        return []

    job_profiles = []
    for file_path in sorted(data_dir.glob("*.json")):
        with file_path.open(encoding="utf-8") as file:
            job_profiles.append(json.load(file))

    return job_profiles


def extract_skill_names_from_job_profile(job_profile: dict) -> list[str]:
    """Collect all skill-like fields from one extracted job profile."""
    skills = []

    for item in job_profile.get("strongly_required_skills", []):
        if isinstance(item, dict):
            skills.append(item.get("skill", ""))
        else:
            skills.append(item)

    for field_name in [
        "required_skills",
        "preferred_skills",
        "soft_skills",
        "tools_and_platforms",
    ]:
        skills.extend(job_profile.get(field_name, []))

    return [normalize_skill(skill) for skill in skills if isinstance(skill, str) and skill.strip()]


def load_esco_terms(path: Path = ESCO_TERMS_PATH, min_words: int = 1) -> list[str]:
    """Load ESCO skill terms if you want a broader extraction vocabulary."""
    if not path.exists():
        return []

    terms = []
    for line in path.read_text(encoding="utf-8").splitlines():
        term = normalize_skill(line)
        if term and len(term.split()) >= min_words:
            terms.append(term)

    return terms


def build_skill_vocabulary(
    job_profiles: list[dict] | None = None,
    include_esco_terms: bool = False,
) -> list[str]:
    """Build the skill vocabulary used for CV extraction."""
    profiles = job_profiles if job_profiles is not None else load_job_profiles()
    vocabulary = []

    for profile in profiles:
        vocabulary.extend(extract_skill_names_from_job_profile(profile))

    if include_esco_terms:
        vocabulary.extend(load_esco_terms(min_words=2))

    skill_aliases = load_skill_aliases()
    generic_skill_terms = load_generic_skill_terms()

    vocabulary.extend(skill_aliases.values())
    vocabulary.extend(_expand_composite_skill_variants(vocabulary))

    unique_vocabulary = {
        normalize_skill(skill)
        for skill in vocabulary
        if skill and normalize_text(normalize_skill(skill)) not in generic_skill_terms
    }

    return sorted(unique_vocabulary, key=lambda skill: (len(skill.split()), skill.lower()), reverse=True)


def _expand_composite_skill_variants(skills: list[str]) -> list[str]:
    """Expand labels like JavaScript/TypeScript so each part can be detected in a CV."""
    variants = []

    for skill in skills:
        normalized_skill = normalize_skill(skill)
        if "/" in normalized_skill:
            variants.extend(part.strip() for part in normalized_skill.split("/") if part.strip())

        if "," in normalized_skill:
            variants.extend(part.strip() for part in normalized_skill.split(",") if part.strip())

    return variants


def _skill_pattern(skill: str) -> re.Pattern:
    """Create a regex pattern that matches a skill as a phrase, not as part of another word."""
    escaped_skill = re.escape(skill.lower())
    escaped_skill = escaped_skill.replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![a-z0-9]){escaped_skill}(?![a-z0-9])", re.IGNORECASE)


def extract_skills_from_text(cv_text: str, vocabulary: list[str] | None = None) -> list[str]:
    """Extract candidate skills from CV text using phrase matching against the vocabulary."""
    normalized_cv_text = normalize_text(cv_text)
    skill_vocabulary = vocabulary if vocabulary is not None else build_skill_vocabulary()
    found_skills = []

    for skill in skill_vocabulary:
        normalized_skill = normalize_skill(skill)
        if not normalized_skill:
            continue

        if _skill_pattern(normalized_skill).search(normalized_cv_text):
            found_skills.append(normalized_skill)

    skill_aliases = load_skill_aliases()
    generic_skill_terms = load_generic_skill_terms()

    for alias, canonical_skill in skill_aliases.items():
        if _skill_pattern(alias).search(normalized_cv_text):
            found_skills.append(canonical_skill)

    unique_skills = {
        normalize_skill(skill)
        for skill in found_skills
        if skill and normalize_text(normalize_skill(skill)) not in generic_skill_terms
    }

    return sorted(unique_skills, key=str.lower)


def extract_candidate_skill_profile(
    cv_text: str,
    job_profiles: list[dict] | None = None,
    include_esco_terms: bool = False,
) -> CandidateSkillProfile:
    """Extract the candidate email, estimated experience, and skills from CV text."""
    cv_analysis = analyze_cv(cv_text)
    vocabulary = build_skill_vocabulary(
        job_profiles=job_profiles,
        include_esco_terms=include_esco_terms,
    )

    return CandidateSkillProfile(
        email=cv_analysis.get("email"),
        estimated_experience_years=cv_analysis.get("estimated_experience_years", 0),
        skills=extract_skills_from_text(cv_text, vocabulary=vocabulary),
    )


def save_candidate_skill_profile(profile: CandidateSkillProfile, output_path: str | Path) -> Path:
    """Save an extracted candidate skill profile as JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(profile.model_dump_json(indent=4), encoding="utf-8")
    return path


def main() -> None:
    """Run CV skill extraction as an individual command-line module."""
    parser = argparse.ArgumentParser(description="Extract a candidate skill profile from a CV.")
    parser.add_argument("cv_file", help="Path to a PDF or TXT CV file.")
    parser.add_argument(
        "--job-skills-dir",
        type=Path,
        default=DEFAULT_JOB_SKILLS_DIR,
        help="Directory containing extracted job skill JSON files used as vocabulary.",
    )
    parser.add_argument(
        "--include-esco",
        action="store_true",
        help="Also include ESCO terms in the extraction vocabulary.",
    )
    parser.add_argument("--output", help="Optional path to save the candidate profile JSON.")
    args = parser.parse_args()

    job_profiles = load_job_profiles(args.job_skills_dir)
    profile = extract_candidate_skill_profile(
        read_cv_text(args.cv_file),
        job_profiles=job_profiles,
        include_esco_terms=args.include_esco,
    )

    if args.output:
        save_candidate_skill_profile(profile, args.output)
    else:
        print(profile.model_dump_json(indent=4))


if __name__ == "__main__":
    main()
