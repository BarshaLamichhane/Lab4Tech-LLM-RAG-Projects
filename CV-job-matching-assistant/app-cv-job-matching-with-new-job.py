import json
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from src.cv.cv_parser import extract_text_from_pdf
from src.cv.cv_skill_extractor import extract_candidate_skill_profile
from src.job_description.job_description_cleaner_mistral_api import extract_job_skills, save_extracted_skills
from src.matching.skill_matching_engine import (
    DEFAULT_JOB_SKILLS_DIR,
    calculate_skill_match,
    get_saved_job_profile_by_role,
    load_saved_job_profiles,
    rank_candidate_against_saved_jobs,
)


st.set_page_config(page_title="CV Job Matcher", layout="wide")


def read_uploaded_text_file(uploaded_file) -> str:
    """Read text from an uploaded PDF or TXT file."""
    if uploaded_file is None:
        return ""

    if uploaded_file.type == "application/pdf" or uploaded_file.name.lower().endswith(".pdf"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(uploaded_file.read())
            temp_path = temp_file.name

        try:
            return extract_text_from_pdf(temp_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    return uploaded_file.read().decode("utf-8", errors="ignore")


def read_uploaded_job_description(uploaded_file) -> str:
    """Read text from an uploaded TXT job-description file."""
    if uploaded_file is None:
        return ""

    return uploaded_file.read().decode("utf-8", errors="ignore")


def make_match_table(match_results: list[dict]) -> pd.DataFrame:
    """Convert saved-job match results into a compact table."""
    return pd.DataFrame(
        [
            {
                "Role": result["target_role"],
                "Match %": result["score"],
                "Matched Strong Skills": len(result["matched_strongly_required_skills"]),
                "Missing Strong Skills": len(result["missing_strongly_required_skills"]),
                "Matched Skills": len(result["matched_skills"]),
                "Missing Skills": len(result["missing_skills"]),
            }
            for result in match_results
        ]
    )


def show_skill_list(title: str, skills: list[str]) -> None:
    """Render a compact skill list."""
    st.markdown(f"**{title}**")
    if not skills:
        st.caption("None")
        return

    for skill in skills:
        st.write(f"- {skill}")


def show_candidate_profile(candidate_profile: dict) -> None:
    """Show extracted CV metadata and skills."""
    st.subheader("Extracted Candidate Profile")

    col_left, col_right = st.columns(2)
    col_left.metric("Estimated Experience Years", candidate_profile["estimated_experience_years"])
    col_right.write(f"**Email:** {candidate_profile['email'] or 'Not found'}")

    show_skill_list("Extracted Candidate Skills", candidate_profile["skills"])


def show_target_match(target_match: dict) -> None:
    """Show detailed selected-job match results."""
    st.subheader("Target Job Match")

    metric_cols = st.columns(3)
    metric_cols[0].metric("Match", f"{target_match['score']}%")
    metric_cols[1].metric("Matched Weight", target_match["matched_weight"])
    metric_cols[2].metric("Possible Weight", target_match["total_possible_weight"])
    st.progress(min(target_match["score"] / 100, 1.0))

    col_left, col_right = st.columns(2)
    with col_left:
        show_skill_list("Matched Strongly Required Skills", target_match["matched_strongly_required_skills"])
        show_skill_list("Matched Skills", target_match["matched_skills"])

    with col_right:
        show_skill_list("Missing Strongly Required Skills", target_match["missing_strongly_required_skills"])
        show_skill_list("Missing Skills", target_match["missing_skills"])


def clear_previous_results() -> None:
    """Clear old match results before calculating a fresh target match."""
    for key in [
        "match_candidate_profile",
        "match_target_job_profile",
        "match_target_match",
        "match_target_label",
        "match_all_saved_jobs",
    ]:
        st.session_state.pop(key, None)


def refresh_saved_target_match(selected_role: str) -> None:
    """Recalculate the displayed target match when the user selects another saved role."""
    if not selected_role or "match_candidate_profile" not in st.session_state:
        return

    if st.session_state.get("match_target_label") == selected_role:
        return

    target_job_profile = get_saved_job_profile_by_role(selected_role, DEFAULT_JOB_SKILLS_DIR)
    target_match = calculate_skill_match(
        st.session_state["match_candidate_profile"],
        target_job_profile,
    )

    st.session_state["match_target_job_profile"] = target_job_profile
    st.session_state["match_target_match"] = target_match.model_dump()
    st.session_state["match_target_label"] = selected_role
    st.session_state.pop("match_all_saved_jobs", None)


def resolve_target_job_profile(
    target_mode: str,
    selected_role: str,
    job_description_text: str,
    save_new_job_profile: bool,
) -> tuple[dict, str]:
    """Return the target job profile from saved JSON or a newly extracted job description."""
    if target_mode == "Select available job description":
        return get_saved_job_profile_by_role(selected_role, DEFAULT_JOB_SKILLS_DIR), selected_role

    if not job_description_text.strip():
        raise ValueError("Upload or paste a new job description before calculating the match.")

    extracted_job_skills = extract_job_skills(job_description_text)
    if save_new_job_profile:
        save_extracted_skills(extracted_job_skills, DEFAULT_JOB_SKILLS_DIR)

    job_profile = extracted_job_skills.model_dump()
    return job_profile, job_profile.get("role", "New job description")


def main() -> None:
    """Run the Streamlit app for CV matching with saved or new job descriptions."""
    st.title("CV Job Matching Engine")
    st.write("Compare a candidate CV with an existing extracted job or a newly uploaded job description.")

    saved_job_profiles = load_saved_job_profiles(DEFAULT_JOB_SKILLS_DIR)

    with st.sidebar:
        st.header("Candidate CV")
        uploaded_cv_file = st.file_uploader("Upload CV", type=["pdf", "txt"])
        pasted_cv_text = st.text_area("Or paste CV text", height=220)

        st.header("Target Job")
        target_mode = st.radio(
            "Job description source",
            ["Select available job description", "Upload new job description"],
        )

        selected_role = ""
        uploaded_job_file = None
        pasted_job_description = ""
        save_new_job_profile = False

        if target_mode == "Select available job description":
            if not saved_job_profiles:
                st.warning(f"No saved job profiles found in {DEFAULT_JOB_SKILLS_DIR}")
            else:
                selected_role = st.selectbox("Existing role", sorted(saved_job_profiles))
        else:
            uploaded_job_file = st.file_uploader("Upload job description", type=["txt"])
            pasted_job_description = st.text_area("Or paste job description", height=220)
            save_new_job_profile = st.checkbox("Save extracted job profile for future matching", value=True)

    cv_text = pasted_cv_text.strip() or read_uploaded_text_file(uploaded_cv_file).strip()
    job_description_text = pasted_job_description.strip() or read_uploaded_job_description(uploaded_job_file).strip()

    if cv_text:
        st.subheader("CV Text Preview")
        st.text_area("Candidate CV text", cv_text, height=180)
    else:
        st.info("Upload a CV or paste CV text to begin.")

    if target_mode == "Upload new job description" and job_description_text:
        st.subheader("New Job Description Preview")
        st.text_area("Job description text", job_description_text, height=180)

    if st.button("Calculate Match", type="primary", disabled=not cv_text):
        clear_previous_results()
        try:
            with st.spinner("Preparing job profile, extracting CV skills, and calculating target match..."):
                target_job_profile, target_label = resolve_target_job_profile(
                    target_mode=target_mode,
                    selected_role=selected_role,
                    job_description_text=job_description_text,
                    save_new_job_profile=save_new_job_profile,
                )
                vocabulary_profiles = list(saved_job_profiles.values()) + [target_job_profile]
                candidate_profile = extract_candidate_skill_profile(
                    cv_text,
                    job_profiles=vocabulary_profiles,
                )
                target_match = calculate_skill_match(candidate_profile, target_job_profile)

            st.session_state["match_candidate_profile"] = candidate_profile.model_dump()
            st.session_state["match_target_job_profile"] = target_job_profile
            st.session_state["match_target_match"] = target_match.model_dump()
            st.session_state["match_target_label"] = target_label
        except Exception as exc:
            st.error(str(exc))

    if target_mode == "Select available job description":
        try:
            refresh_saved_target_match(selected_role)
        except Exception as exc:
            st.error(str(exc))

    if "match_candidate_profile" in st.session_state:
        result = {
            "candidate_profile": st.session_state["match_candidate_profile"],
            "target_job_match": st.session_state["match_target_match"],
            "target_job_profile": st.session_state["match_target_job_profile"],
        }

        show_candidate_profile(result["candidate_profile"])
        show_target_match(result["target_job_match"])

        if st.button("Show Other Fit"):
            with st.spinner("Calculating match against all saved jobs..."):
                all_saved_job_matches = [
                    match_result.model_dump()
                    for match_result in rank_candidate_against_saved_jobs(
                        st.session_state["match_candidate_profile"],
                        DEFAULT_JOB_SKILLS_DIR,
                    )
                ]

            st.session_state["match_all_saved_jobs"] = all_saved_job_matches

        if "match_all_saved_jobs" in st.session_state:
            st.subheader("Match Against All Saved Jobs")
            match_table = make_match_table(st.session_state["match_all_saved_jobs"])
            st.dataframe(match_table, use_container_width=True, hide_index=True)
            result["all_saved_job_matches"] = st.session_state["match_all_saved_jobs"]

        with st.expander("Target Job Profile JSON"):
            st.json(st.session_state["match_target_job_profile"])

        with st.expander("Full Match JSON"):
            st.json(result)

        st.download_button(
            label="Download Match JSON",
            data=json.dumps(result, indent=4),
            file_name=f"{st.session_state['match_target_label'].lower().replace(' ', '_')}_cv_match.json",
            mime="application/json",
        )


if __name__ == "__main__":
    main()
