"""Extract candidate skills from CV text using a controlled skill vocabulary."""

from __future__ import annotations

import argparse
import json
import re
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field
from backend.job_description.job_profile_catalog import profile_paths

try:
    from backend.cv.cv_analyzer import analyze_cv
    from backend.cv.cv_parser import read_cv_text
except ModuleNotFoundError:
    from backend.cv.cv_analyzer import analyze_cv
    from backend.cv.cv_parser import read_cv_text


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_JOB_SKILLS_DIR = PROJECT_ROOT / "data" / "extracted_skills_mistral-large-latest"
ESCO_TERMS_PATH = PROJECT_ROOT / "data" / "taxonomies" / "esco" / "skills_en_terms.txt"
SKILL_CATEGORIES_PATH = PROJECT_ROOT / "data" / "taxonomies" / "skill_categories.json"
PROJECT_SECTION_HEADINGS = {
    "projects",
    "project experience",
    "personal projects",
    "academic projects",
    "selected projects",
    "key projects",
}
CV_SECTION_HEADINGS = PROJECT_SECTION_HEADINGS | {
    "education",
    "experience",
    "professional experience",
    "work experience",
    "employment",
    "skills",
    "technical skills",
    "certifications",
    "awards",
    "publications",
    "languages",
    "interests",
    "summary",
    "profile",
}
OUTCOME_TERMS = {
    "achieved",
    "improved",
    "increased",
    "reduced",
    "decreased",
    "saved",
    "delivered",
    "resulted",
    "accuracy",
    "performance",
    "latency",
    "users",
}


class CandidateProject(BaseModel):
    """One project parsed from an explicitly labelled CV project section."""

    name: str
    description: str = ""
    role: str = ""
    skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    outcomes: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)


class CandidateSkillProfile(BaseModel):
    """Structured skill profile extracted from a candidate CV."""

    email: str | None = None
    estimated_experience_years: int = 0
    skills: list[str] = Field(default_factory=list)
    projects: list[CandidateProject] = Field(default_factory=list)


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
    for file_path in profile_paths(data_dir):
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

    unique_vocabulary = _unique_skills(
        skill
        for skill in vocabulary
        if skill and normalize_text(normalize_skill(skill)) not in generic_skill_terms
    )

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

    unique_skills = _unique_skills(
        skill
        for skill in found_skills
        if skill and normalize_text(normalize_skill(skill)) not in generic_skill_terms
    )

    return sorted(unique_skills, key=str.lower)


def _unique_skills(skills) -> list[str]:
    """Deduplicate skills case-insensitively while preserving readable labels."""
    unique = {}
    for skill in skills:
        normalized_skill = normalize_skill(skill)
        key = normalize_text(normalized_skill)
        if key and key not in unique:
            unique[key] = normalized_skill
    return list(unique.values())


def extract_projects_from_text(
    cv_text: str,
    vocabulary: list[str] | None = None,
) -> list[CandidateProject]:
    """Parse structured projects without an LLM from an explicitly named project section."""
    project_lines = _project_section_lines(cv_text)
    if not project_lines:
        return []

    skill_vocabulary = vocabulary if vocabulary is not None else build_skill_vocabulary()
    projects = []
    for block in _project_blocks(project_lines):
        project = _project_from_block(block, skill_vocabulary)
        if project:
            projects.append(project)
    return projects


def _project_section_lines(cv_text: str) -> list[str]:
    lines = [line.strip() for line in cv_text.splitlines()]
    section_start = None
    for index, line in enumerate(lines):
        if _heading_key(line) in PROJECT_SECTION_HEADINGS:
            section_start = index + 1
            break
    if section_start is None:
        return []

    section_lines = []
    for line in lines[section_start:]:
        if line and _heading_key(line) in CV_SECTION_HEADINGS:
            break
        section_lines.append(line)
    return section_lines


def _project_blocks(lines: list[str]) -> list[list[str]]:
    blocks = []
    current = []
    for line in lines:
        if not line:
            if current:
                blocks.append(current)
                current = []
            continue
        if current and _looks_like_project_title(line) and any(_is_bullet(item) for item in current[1:]):
            blocks.append(current)
            current = []
        current.append(line)
    if current:
        blocks.append(current)
    return blocks


def _project_from_block(block: list[str], vocabulary: list[str]) -> CandidateProject | None:
    if not block:
        return None
    name = _clean_project_name(block[0])
    if not name or _is_bullet(block[0]) or _label_value(block[0], "role") is not None:
        return None

    links = sorted(set(re.findall(r"https?://[^\s,;]+|www\.[^\s,;]+", "\n".join(block))))
    role = ""
    descriptions = []
    responsibilities = []
    outcomes = []

    for raw_line in block[1:]:
        line = _strip_bullet(raw_line)
        if not line:
            continue
        role_value = _label_value(line, "role")
        if role_value is not None:
            role = role_value
            continue
        if re.match(r"^(technologies|technology|tech stack|tools|skills)\s*:", line, re.IGNORECASE):
            continue
        line_without_links = re.sub(r"https?://[^\s,;]+|www\.[^\s,;]+", "", line).strip(" -|,;")
        if not line_without_links:
            continue
        if _is_outcome(line_without_links):
            outcomes.append(line_without_links)
        elif _is_bullet(raw_line):
            responsibilities.append(line_without_links)
        else:
            descriptions.append(line_without_links)

    block_text = "\n".join(block)
    return CandidateProject(
        name=name,
        description=" ".join(descriptions),
        role=role,
        skills=extract_skills_from_text(block_text, vocabulary=vocabulary),
        responsibilities=_unique_lines(responsibilities),
        outcomes=_unique_lines(outcomes),
        links=links,
    )


def _heading_key(line: str) -> str:
    return re.sub(r"[^a-z ]+", "", line.casefold()).strip()


def _looks_like_project_title(line: str) -> bool:
    stripped = line.strip()
    return (
        bool(stripped)
        and not _is_bullet(stripped)
        and len(stripped) <= 120
        and not stripped.endswith((".", ";"))
        and not re.match(
            r"^(role|technologies|technology|tech stack|tools|skills|description|responsibilities|outcomes?)\s*:",
            stripped,
            re.IGNORECASE,
        )
    )


def _clean_project_name(line: str) -> str:
    without_links = re.sub(r"https?://[^\s,;]+|www\.[^\s,;]+", "", line)
    return re.sub(r"\s*[|–—]\s*(?:19|20)\d{2}.*$", "", without_links).strip(" -|–—")


def _is_bullet(line: str) -> bool:
    return bool(re.match(r"^\s*(?:[-*•▪◦]|(?:\d+)[.)])\s+", line))


def _strip_bullet(line: str) -> str:
    return re.sub(r"^\s*(?:[-*•▪◦]|(?:\d+)[.)])\s+", "", line).strip()


def _label_value(line: str, label: str) -> str | None:
    match = re.match(rf"^{re.escape(label)}\s*:\s*(.+)$", line, re.IGNORECASE)
    return match.group(1).strip() if match else None


def _is_outcome(line: str) -> bool:
    normalized = normalize_text(line)
    return bool(re.search(r"\b\d+(?:\.\d+)?\s*%", line)) or any(
        re.search(rf"\b{re.escape(term)}\b", normalized)
        for term in OUTCOME_TERMS
    )


def _unique_lines(lines: list[str]) -> list[str]:
    return list(dict.fromkeys(line for line in lines if line))


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
        projects=extract_projects_from_text(cv_text, vocabulary=vocabulary),
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
