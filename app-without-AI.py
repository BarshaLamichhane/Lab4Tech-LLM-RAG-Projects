import streamlit as st
import tempfile

# from src.cv_parser import extract_text_from_pdf

# from src.skill_extractor import extract_skills

# from src.job_matcher import calculate_match, suggest_alternative_roles, ROLE_REQUIREMENTS
# from src.rag_pipeline import load_job_role_documents, retrieve_role_context
# from src.llm_service import generate_explanation

###CV Parser (src/cv_parser.py)
import fitz

def extract_text_from_pdf(file_path: str) -> str:
    text = ""

    doc = fitz.open(file_path)

    for page in doc:
        text += page.get_text()
    print(f"Extracted {len(text)} characters from the CV.")
    print(f"Sample text: {text[:200]}...")

    return text.strip()

###Skill Extractor (src/skill_extractor.py)
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

###Job Matcher (src/job_matcher.py)
## This dictionary can be replaced by real role descriptions or requirements loaded from a database or external source. The `calculate_match` function computes how well the user's skills match the required skills for a given role, while the `suggest_alternative_roles` function provides a list of roles sorted by their match score based on the user's skills.
## see data/job_roles/ai_engineer.txt for an example of how role descriptions can be structured and stored for retrieval in the RAG pipeline.
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


###### RAG Pipeline (src/rag_pipeline.py)
from pathlib import Path

def load_job_role_documents(data_dir: str = "data/job_roles") -> dict:
    documents = {}

    for file_path in Path(data_dir).glob("*.txt"):
        role_name = file_path.stem.replace("_", " ").title()

        with open(file_path, "r", encoding="utf-8") as file:
            documents[role_name] = file.read()
    print(f"Loaded {len(documents)} job role documents for RAG retrieval.")
    print(f"Sample document for 'AI Engineer': {documents.get('AI Engineer', '')[:200]}...")
    return documents

role_docs = load_job_role_documents()
print(f"Available job role documents: {list(role_docs.keys())}")
def retrieve_role_context(target_role: str, documents: dict) -> str:
    for role_name, content in documents.items():
        if target_role.lower() in role_name.lower():
            return content

    return ""

##### LLM Service (src/llm_service.py)

def generate_explanation(match_result: dict, role_context: str = "") -> str:
    score = match_result["score"]
    role = match_result["target_role"]
    matched = ", ".join(match_result["matched_skills"])
    missing = ", ".join(match_result["missing_skills"])

    return f"""

The CV shows a {score}% match for the role of {role}.

Strong matching areas:
{matched if matched else "No strong matching skills detected."}

Missing or weaker areas:
{missing if missing else "No major missing skills detected."}

Recommendation:
The candidate should strengthen the missing skills to improve suitability for this role.
""".strip()

######## Frontend Application (app.py) )
print("Starting the frontend application...")

st.set_page_config(
    page_title="Lab4Tech CV-RAG Assistantt",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Lab4Tech CV-to-Job Matching Assistantt")

st.info(
    "Transparency notice: You are interacting with an AI-assisted system. "
    "Uploaded CVs are processed only during this prototype session."
)

st.sidebar.header("Configuration")

target_role = st.sidebar.selectbox(
    "Select target job field",
    list(ROLE_REQUIREMENTS.keys())
)

uploaded_cv = st.file_uploader(
    "Upload CV",
    type=["pdf"]
)

if uploaded_cv:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_cv.read())
        cv_path = tmp.name

    cv_text = extract_text_from_pdf(cv_path)
    user_skills = extract_skills(cv_text)

    match_result = calculate_match(user_skills, target_role)
    alternative_roles = suggest_alternative_roles(user_skills)

    role_docs = load_job_role_documents()
    print(f"Available job role documents: {list(role_docs.keys())}")
    role_context = retrieve_role_context(target_role, role_docs)

    explanation = generate_explanation(match_result, role_context)

    st.success("CV analyzed successfully.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Match Score")
        st.metric(
            label=f"{target_role} Match",
            value=f"{match_result['score']}%"
        )
        st.progress(match_result["score"] / 100)

    with col2:
        st.subheader("Detected Skills")
        st.write(user_skills)

    st.subheader("Matching Skills")
    st.write(match_result["matched_skills"])

    st.subheader("Missing Skills")
    st.write(match_result["missing_skills"])

    st.subheader("AI Explanation")
    st.write(explanation)

    st.subheader("Suggested Alternative Roles")

    for item in alternative_roles[:3]:
        st.write(f"**{item['role']}** — {item['score']}% match")

    with st.expander("View extracted CV text"):
        st.text(cv_text[:5000])

else:
    st.warning("Please upload a CV to start.")