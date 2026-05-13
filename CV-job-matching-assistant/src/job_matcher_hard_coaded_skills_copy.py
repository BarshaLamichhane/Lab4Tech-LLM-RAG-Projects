"""use in app-without-AI.py for hard coded skills matching without RAG retrieval"""
## This dictionary can be replaced by real role descriptions or requirements loaded from a database or external source. The `calculate_match` function computes how well the user's skills match the required skills for a given role, while the `suggest_alternative_roles` function provides a list of roles sorted by their match score based on the user's skills.
## see data/job_roles/ai_engineer.txt for an example of how role descriptions can be structured and stored for retrieval in the RAG pipeline.
## This was used for scoring the match between the extracted skills from the CV and the required skills for the target role. The `calculate_match` function computes the percentage match and identifies which skills are matched and which are missing. The `suggest_alternative_roles` function provides a list of roles sorted by their match score based on the user's skills, allowing for recommendations of other suitable roles.
ROLE_REQUIREMENTS = {
    "AI Engineer": [
        "python", "machine learning", "deep learning",
        "llm", "rag", "langchain", "docker", "fastapi"
    ],
    "Data Scientist": [
        "python", "sql", "machine learning",
        "statistics", "scikit-learn", "data analysis"
    ],
    "Data Engineer": [
        "python", "sql", "docker", "linux", "aws"
    ],
    "Business Analyst": [
        "sql", "data analysis", "power bi", "statistics"
    ],
    "Software Engineer": [
        "python", "git", "docker", "react", "angular"
    ]
}


def calculate_match(user_skills: list[str], target_role: str) -> dict:
    required_skills = ROLE_REQUIREMENTS.get(target_role, [])

    matched_skills = sorted(list(set(user_skills) & set(required_skills)))
    missing_skills = sorted(list(set(required_skills) - set(user_skills)))

    score = 0

    if required_skills:
        score = round((len(matched_skills) / len(required_skills)) * 100, 2)

    return {
        "target_role": target_role,
        "score": score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "required_skills": required_skills
    }


def suggest_alternative_roles(user_skills: list[str]) -> list[dict]:
    suggestions = []

    for role in ROLE_REQUIREMENTS:
        result = calculate_match(user_skills, role)
        suggestions.append({
            "role": role,
            "score": result["score"]
        })

    return sorted(suggestions, key=lambda x: x["score"], reverse=True)