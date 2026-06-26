"""Evaluate saved Mistral job-description extraction output.

This evaluator compares saved job profile JSON files from
data/extracted_skills_mistral-large-latest/ against manually labeled gold
skills in evaluation/expected_job_skills.json.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any

from backend.cv.cv_skill_extractor import normalize_skill
from backend.job_description.job_profile_catalog import profile_paths
from backend.matching.skill_matching_engine import skills_match


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVALUATION_DIR = PROJECT_ROOT / "evaluation"
EXPECTED_PATH = EVALUATION_DIR / "expected_job_skills.json"
REPORTS_DIR = EVALUATION_DIR / "reports"
SAVED_JOB_PROFILE_DIR = PROJECT_ROOT / "data" / "extracted_skills_mistral-large-latest"

SKILL_CATEGORIES = [
    "strongly_required_skills",
    "required_skills",
    "preferred_skills",
    "tools_and_platforms",
]


def main() -> None:
    expected_data = _load_json(EXPECTED_PATH)
    cases = expected_data.get("cases", [])
    if not cases:
        raise ValueError(f"No evaluation cases found in {EXPECTED_PATH}")

    case_reports = [_evaluate_case(case) for case in cases]
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_file": str(EXPECTED_PATH.relative_to(PROJECT_ROOT)),
        "summary": _summarize(case_reports),
        "cases": case_reports,
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    json_report_path = REPORTS_DIR / "job_description_evaluation_report.json"
    markdown_report_path = REPORTS_DIR / "job_description_evaluation_report.md"
    json_report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    markdown_report_path.write_text(_render_markdown(report), encoding="utf-8")

    print(_render_console_summary(report))
    print(f"\nJSON report: {json_report_path.relative_to(PROJECT_ROOT)}")
    print(f"Markdown report: {markdown_report_path.relative_to(PROJECT_ROOT)}")


def _evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    profile_lookup = _find_saved_profile(case)
    if profile_lookup is None:
        return {
            "case_id": case["case_id"],
            "status": "not_found",
            "message": "No saved Mistral-extracted job profile found for this case.",
            "expected_role": case.get("expected_role", ""),
            "expected_company": case.get("expected_company", ""),
            "expected_profile_file": case.get("saved_profile_file", ""),
        }

    profile_path, job_profile, match_level = profile_lookup
    actual_skills = _job_profile_skills_by_category(job_profile)
    expected_skills = case["expected_job_skills"]
    category_reports = {
        category: _compare_skill_lists(
            expected=expected_skills.get(category, []),
            actual=actual_skills.get(category, []),
        )
        for category in SKILL_CATEGORIES
    }

    return {
        "case_id": case["case_id"],
        "status": "evaluated",
        "profile_file": str(profile_path.relative_to(PROJECT_ROOT)),
        "profile_match_level": match_level,
        "expected_role": case.get("expected_role", ""),
        "actual_role": job_profile.get("role", ""),
        "role_match": _same_lookup_text(case.get("expected_role", ""), job_profile.get("role", "")),
        "expected_company": case.get("expected_company", ""),
        "actual_company": job_profile.get("company_name", ""),
        "company_match": _same_lookup_text(case.get("expected_company", ""), job_profile.get("company_name", "")),
        "expected_company_context": case.get("expected_company_context", ""),
        "actual_company_context": job_profile.get("company_context", ""),
        "company_context_contains_expected_terms": _contains_meaningful_terms(
            source=job_profile.get("company_context", ""),
            expected=case.get("expected_company_context", ""),
        ),
        "overall": _compare_skill_lists(
            expected=_flatten_skills(expected_skills),
            actual=_flatten_skills(actual_skills),
        ),
        "categories": category_reports,
        "actual_skills": actual_skills,
    }


def _find_saved_profile(case: dict[str, Any]) -> tuple[Path, dict[str, Any], str] | None:
    expected_filename = str(case.get("saved_profile_file", "")).strip()
    if expected_filename:
        profile_path = SAVED_JOB_PROFILE_DIR / expected_filename
        if profile_path.is_file():
            return profile_path, _load_json(profile_path), "explicit_file"

    expected_role = _normalize_lookup_text(case.get("expected_role", ""))
    expected_company = _normalize_lookup_text(case.get("expected_company", ""))
    role_only_match = None

    for profile_path in profile_paths(SAVED_JOB_PROFILE_DIR):
        job_profile = _load_json(profile_path)
        actual_role = _normalize_lookup_text(job_profile.get("role", ""))
        actual_company = _normalize_lookup_text(job_profile.get("company_name", ""))
        if actual_role != expected_role:
            continue

        if expected_company and actual_company == expected_company:
            return profile_path, job_profile, "role_and_company"

        if role_only_match is None:
            role_only_match = (profile_path, job_profile, "role_only")

    return role_only_match


def _job_profile_skills_by_category(job_profile: dict[str, Any]) -> dict[str, list[str]]:
    return {
        "strongly_required_skills": [
            item.get("skill", "")
            if isinstance(item, dict)
            else item
            for item in job_profile.get("strongly_required_skills", [])
        ],
        "required_skills": job_profile.get("required_skills", []),
        "preferred_skills": job_profile.get("preferred_skills", []),
        "tools_and_platforms": job_profile.get("tools_and_platforms", []),
    }


def _compare_skill_lists(expected: list[str], actual: list[str]) -> dict[str, Any]:
    expected = _unique_skills(expected)
    actual = _unique_skills(actual)
    matched_pairs = _match_pairs(expected, actual)
    matched_expected = [expected_skill for expected_skill, _ in matched_pairs]
    matched_actual = [actual_skill for _, actual_skill in matched_pairs]
    missing = [
        expected_skill
        for expected_skill in expected
        if not any(skills_match(expected_skill, matched) for matched in matched_expected)
    ]
    unexpected = [
        actual_skill
        for actual_skill in actual
        if not any(skills_match(actual_skill, matched) for matched in matched_actual)
    ]

    precision = _safe_ratio(len(matched_actual), len(actual))
    recall = _safe_ratio(len(matched_expected), len(expected))
    f1 = 0.0 if precision + recall == 0 else (2 * precision * recall) / (precision + recall)

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "expected_count": len(expected),
        "actual_count": len(actual),
        "matched_count": len(matched_pairs),
        "matched_pairs": [
            {"expected": expected_skill, "actual": actual_skill}
            for expected_skill, actual_skill in matched_pairs
        ],
        "missing_expected": missing,
        "unexpected_actual": unexpected,
    }


def _match_pairs(expected: list[str], actual: list[str]) -> list[tuple[str, str]]:
    pairs = []
    used_actual_indexes = set()
    for expected_skill in expected:
        for index, actual_skill in enumerate(actual):
            if index in used_actual_indexes:
                continue
            if skills_match(actual_skill, expected_skill):
                pairs.append((expected_skill, actual_skill))
                used_actual_indexes.add(index)
                break
    return pairs


def _summarize(case_reports: list[dict[str, Any]]) -> dict[str, Any]:
    evaluated_cases = [case for case in case_reports if case["status"] == "evaluated"]
    missing_cases = [case for case in case_reports if case["status"] != "evaluated"]
    overall_f1_scores = [case["overall"]["f1"] for case in evaluated_cases]
    category_f1_scores = [
        category_report["f1"]
        for case in evaluated_cases
        for category_report in case["categories"].values()
    ]

    return {
        "case_count": len(case_reports),
        "evaluated_case_count": len(evaluated_cases),
        "missing_profile_count": len(missing_cases),
        "average_overall_f1": round(mean(overall_f1_scores), 4) if overall_f1_scores else None,
        "average_category_f1": round(mean(category_f1_scores), 4) if category_f1_scores else None,
    }


def _render_console_summary(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "HireReadyAI job-description extraction evaluation",
        f"Cases: {summary['case_count']}",
        f"Evaluated saved profiles: {summary['evaluated_case_count']}",
        f"Missing saved profiles: {summary['missing_profile_count']}",
        f"Average overall F1: {summary['average_overall_f1']}",
        f"Average category F1: {summary['average_category_f1']}",
    ]
    for case in report["cases"]:
        if case["status"] != "evaluated":
            lines.append(f"- {case['case_id']}: not found")
            continue
        lines.append(
            f"- {case['case_id']}: f1={case['overall']['f1']}, "
            f"profile={case['profile_file']} ({case['profile_match_level']})"
        )
    return "\n".join(lines)


def _render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# HireReadyAI Job-Description Extraction Evaluation",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- Cases: `{summary['case_count']}`",
        f"- Evaluated saved profiles: `{summary['evaluated_case_count']}`",
        f"- Missing saved profiles: `{summary['missing_profile_count']}`",
        f"- Average overall F1: `{summary['average_overall_f1']}`",
        f"- Average category F1: `{summary['average_category_f1']}`",
        "",
        "## Cases",
        "",
    ]

    for case in report["cases"]:
        lines.append(f"### {case['case_id']}")
        lines.append("")
        if case["status"] != "evaluated":
            lines.append("Saved Mistral profile: `not found`")
            lines.append("")
            continue

        lines.extend(
            [
                f"- Profile file: `{case['profile_file']}`",
                f"- Profile match level: `{case['profile_match_level']}`",
                f"- Role match: `{case['role_match']}`",
                f"- Company match: `{case['company_match']}`",
                f"- Company context contains expected terms: `{case['company_context_contains_expected_terms']}`",
                f"- Overall F1: `{case['overall']['f1']}`",
                "",
            ]
        )

        for category, category_report in case["categories"].items():
            lines.append(f"`{category}` F1: `{category_report['f1']}`")
            if category_report["missing_expected"]:
                lines.append(f"- Missing expected: {', '.join(category_report['missing_expected'])}")
            if category_report["unexpected_actual"]:
                lines.append(f"- Unexpected actual: {', '.join(category_report['unexpected_actual'])}")
            lines.append("")

    return "\n".join(lines)


def _flatten_skills(skills_by_category: dict[str, list[str]]) -> list[str]:
    skills = []
    for category in SKILL_CATEGORIES:
        skills.extend(skills_by_category.get(category, []))
    return _unique_skills(skills)


def _unique_skills(skills: list[str]) -> list[str]:
    unique = {}
    for skill in skills:
        if not isinstance(skill, str):
            continue
        normalized_skill = normalize_skill(skill)
        key = normalized_skill.casefold()
        if key and key not in unique:
            unique[key] = normalized_skill
    return list(unique.values())


def _contains_meaningful_terms(source: str, expected: str) -> bool:
    source_tokens = _meaningful_tokens(source)
    expected_tokens = _meaningful_tokens(expected)
    if not expected_tokens:
        return True
    return len(source_tokens & expected_tokens) >= max(1, min(3, len(expected_tokens)))


def _meaningful_tokens(value: str) -> set[str]:
    stopwords = {"and", "for", "the", "with", "that", "this", "into", "from", "they", "are"}
    return {
        token
        for token in _normalize_lookup_text(value).split()
        if len(token) >= 4 and token not in stopwords
    }


def _same_lookup_text(left: str, right: str) -> bool:
    return _normalize_lookup_text(left) == _normalize_lookup_text(right)


def _normalize_lookup_text(value: str) -> str:
    return " ".join("".join(character if character.isalnum() else " " for character in str(value).casefold()).split())


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0 if numerator == 0 else 0.0
    return numerator / denominator


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
