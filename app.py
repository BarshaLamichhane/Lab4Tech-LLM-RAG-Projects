import streamlit as st
import tempfile

from src.cv_parser import extract_text_from_pdf

from src.skill_extractor import extract_skills

from src.job_matcher import calculate_match, suggest_alternative_roles, ROLE_REQUIREMENTS
from src.rag_pipeline import load_job_role_documents, retrieve_role_context
from src.llm_service import generate_explanation

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