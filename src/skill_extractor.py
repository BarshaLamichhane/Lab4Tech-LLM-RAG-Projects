SKILLS_DB = [
    "python", "sql", "machine learning", "deep learning",
    "nlp", "llm", "rag", "langchain", "faiss",
    "pytorch", "tensorflow", "scikit-learn",
    "docker", "fastapi", "streamlit",
    "azure", "aws", "git", "linux",
    "data analysis", "statistics", "power bi",
    "react", "angular"
]


def extract_skills(text: str) -> list[str]:
    text = text.lower()

    found_skills = []

    for skill in SKILLS_DB:
        if skill in text:
            found_skills.append(skill)

    return sorted(list(set(found_skills)))