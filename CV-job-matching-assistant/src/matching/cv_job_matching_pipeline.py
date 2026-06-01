"""Combined pipeline for job extraction, CV skill extraction, and skill matching."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from src.cv.cv_parser import read_cv_text
    from src.cv.cv_skill_extractor import extract_candidate_skill_profile
    from src.job_description.job_description_cleaner_mistral_api import (
        extract_job_skills_from_file,
        save_extracted_skills,
    )
    from src.matching.skill_matching_engine import (
        DEFAULT_JOB_SKILLS_DIR,
        calculate_skill_match,
        get_saved_job_profile_by_role,
        load_job_profile_file,
        load_saved_job_profiles,
        rank_candidate_against_saved_jobs,
        save_match_result,
    )
except ModuleNotFoundError:
    from cv.cv_parser import read_cv_text
    from cv.cv_skill_extractor import extract_candidate_skill_profile
    from job_description.job_description_cleaner_mistral_api import (
        extract_job_skills_from_file,
        save_extracted_skills,
    )
    from matching.skill_matching_engine import (
        DEFAULT_JOB_SKILLS_DIR,
        calculate_skill_match,
        get_saved_job_profile_by_role,
        load_job_profile_file,
        load_saved_job_profiles,
        rank_candidate_against_saved_jobs,
        save_match_result,
    )


def resolve_target_job_profile(
    target_role: str | None = None,
    job_profile_file: str | Path | None = None,
    job_description_file: str | Path | None = None,
    save_extracted_job: bool = False,
    job_skills_dir: Path = DEFAULT_JOB_SKILLS_DIR,
) -> dict:
    """Resolve the target job profile from a saved role, JSON profile, or raw job description."""
    provided_sources = [
        bool(target_role),
        bool(job_profile_file),
        bool(job_description_file),
    ]
    if sum(provided_sources) != 1:
        raise ValueError("Provide exactly one target source: target_role, job_profile_file, or job_description_file.")

    if target_role:
        return get_saved_job_profile_by_role(target_role, job_skills_dir)

    if job_profile_file:
        return load_job_profile_file(job_profile_file)

    extracted_job = extract_job_skills_from_file(job_description_file)
    if save_extracted_job:
        save_extracted_skills(extracted_job, job_skills_dir)

    return extracted_job.model_dump()


def run_cv_job_matching_pipeline(
    cv_file: str | Path,
    target_role: str | None = None,
    job_profile_file: str | Path | None = None,
    job_description_file: str | Path | None = None,
    save_extracted_job: bool = False,
    include_all_saved_jobs: bool = False,
    job_skills_dir: Path = DEFAULT_JOB_SKILLS_DIR,
) -> dict:
    """Run the full CV/job matching pipeline and return a structured result."""
    cv_text = read_cv_text(cv_file)
    target_job_profile = resolve_target_job_profile(
        target_role=target_role,
        job_profile_file=job_profile_file,
        job_description_file=job_description_file,
        save_extracted_job=save_extracted_job,
        job_skills_dir=job_skills_dir,
    )
    saved_job_profiles = list(load_saved_job_profiles(job_skills_dir).values())
    candidate_profile = extract_candidate_skill_profile(
        cv_text,
        job_profiles=saved_job_profiles + [target_job_profile],
    )
    target_match = calculate_skill_match(candidate_profile, target_job_profile)

    result = {
        "candidate_profile": candidate_profile.model_dump(),
        "target_job_profile": target_job_profile,
        "target_job_match": target_match.model_dump(),
    }

    if include_all_saved_jobs:
        result["all_saved_job_matches"] = [
            match_result.model_dump()
            for match_result in rank_candidate_against_saved_jobs(candidate_profile, job_skills_dir)
        ]

    return result


def main() -> None:
    """Run the combined CV/job matching pipeline as a command-line module."""
    parser = argparse.ArgumentParser(description="Run the full CV/job matching pipeline.")
    parser.add_argument("cv_file", help="Path to a PDF or TXT CV file.")
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument("--target-role", help="Role name from saved extracted job profiles.")
    target_group.add_argument("--job-profile-file", help="Path to one extracted job profile JSON file.")
    target_group.add_argument("--job-description-file", help="Path to a raw TXT job-description file.")
    parser.add_argument(
        "--save-extracted-job",
        action="store_true",
        help="Save newly extracted job profiles when --job-description-file is used.",
    )
    parser.add_argument(
        "--job-skills-dir",
        type=Path,
        default=DEFAULT_JOB_SKILLS_DIR,
        help="Directory containing saved extracted job profile JSON files.",
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Also rank the candidate against all saved jobs.",
    )
    parser.add_argument("--output", help="Optional path to save the final JSON result.")
    args = parser.parse_args()

    result = run_cv_job_matching_pipeline(
        cv_file=args.cv_file,
        target_role=args.target_role,
        job_profile_file=args.job_profile_file,
        job_description_file=args.job_description_file,
        save_extracted_job=args.save_extracted_job,
        include_all_saved_jobs=args.show_all,
        job_skills_dir=args.job_skills_dir,
    )

    if args.output:
        save_match_result(result, args.output)
    else:
        print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
