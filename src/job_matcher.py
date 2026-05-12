import json
from pathlib import Path


INPUT_DIR = Path("data/job_roles/cleaned_job_postings")
def load_job_profiles(data_dir: str = "data/extracted_job_skills") -> dict:
    job_profiles = {}
    json_files = list(INPUT_DIR.glob("*.json"))
    print(f"Found {len(json_files)} job profile(s) in {INPUT_DIR}")
    for file_path in json_files:
        if not json_files:
            print("No .json job profiles found in data/cleaned_job_postings/")
            return
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        role = data["role"]
        job_profiles[role] = data

    return job_profiles


def get_all_required_skills(job_profile: dict) -> list[str]:
    skills = []

    skills.extend(job_profile.get("required_skills", []))
    skills.extend(job_profile.get("preferred_skills", []))
    skills.extend(job_profile.get("tools_and_platforms", []))

    return sorted(set([skill.lower() for skill in skills]))


def calculate_match(user_skills: list[str], job_profile: dict) -> dict:
    user_skills_lower = [skill.lower() for skill in user_skills]
    required_skills = get_all_required_skills(job_profile)

    matched_skills = sorted(set(user_skills_lower) & set(required_skills))
    missing_skills = sorted(set(required_skills) - set(user_skills_lower))

    score = 0
    if required_skills:
        score = round((len(matched_skills) / len(required_skills)) * 100, 2)

    return {
        "target_role": job_profile["role"],
        "score": score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "required_skills": required_skills,
    }


def suggest_alternative_roles(user_skills: list[str], job_profiles: dict) -> list[dict]:
    suggestions = []

    for role, profile in job_profiles.items():
        result = calculate_match(user_skills, profile)
        suggestions.append({
            "role": role,
            "score": result["score"]
        })

    return sorted(suggestions, key=lambda x: x["score"], reverse=True)