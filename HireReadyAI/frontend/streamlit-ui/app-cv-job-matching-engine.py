import json
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

import path_setup  # noqa: F401
from backend.cv.cv_parser import extract_text_from_pdf
from backend.cv.cv_skill_extractor import extract_candidate_skill_profile
from backend.matching.skill_matching_engine import (
    DEFAULT_JOB_SKILLS_DIR,
    calculate_skill_match,
    get_saved_job_profile_by_role,
    load_saved_job_profiles,
    rank_candidate_against_saved_jobs,
)

st.set_page_config(page_title="CV Job Matching Engine", layout="wide")


def read_uploaded_cv(uploaded_file) -> str:
    """Read CV text from an uploaded TXT or PDF file."""
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


def make_match_table(match_results: list[dict]) -> pd.DataFrame:
    """Convert all saved-job match results into a display-friendly table."""
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
    """Render a compact bullet list for matched or missing skills."""
    st.markdown(f"**{title}**")
    if not skills:
        st.caption("None")
        return

    for skill in skills:
        st.write(f"- {skill}")


def show_target_match(target_match: dict) -> None:
    """Render the detailed match result for the selected target job."""
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


def show_candidate_profile(candidate_profile: dict) -> None:
    """Render extracted candidate profile information from the CV."""
    st.subheader("Extracted Candidate Profile")

    col_left, col_right = st.columns(2)
    col_left.metric("Estimated Experience Years", candidate_profile["estimated_experience_years"])
    col_right.write(f"**Email:** {candidate_profile['email'] or 'Not found'}")

    show_skill_list("Extracted Candidate Skills", candidate_profile["skills"])


def refresh_selected_target_match(target_role: str) -> None:
    """Recalculate the displayed target match when the selected role changes."""
    if "cv_match_candidate_profile" not in st.session_state:
        return

    if st.session_state.get("cv_match_target_role") == target_role:
        return

    target_job_profile = get_saved_job_profile_by_role(
        target_role,
        DEFAULT_JOB_SKILLS_DIR,
    )
    target_match = calculate_skill_match(
        st.session_state["cv_match_candidate_profile"],
        target_job_profile,
    )

    st.session_state["cv_match_target_match"] = target_match.model_dump()
    st.session_state["cv_match_target_role"] = target_role
    st.session_state.pop("cv_match_all_saved_jobs", None)


def main() -> None:
    """Run the Streamlit CV-to-job matching application."""
    st.title("CV Job Matching Engine")
    st.write("Compare a candidate CV against a target job, then optionally check fit for other saved jobs.")

    saved_job_profiles = load_saved_job_profiles(DEFAULT_JOB_SKILLS_DIR)
    if not saved_job_profiles:
        st.error(f"No saved job profiles found in {DEFAULT_JOB_SKILLS_DIR}")
        return

    with st.sidebar:
        st.header("Inputs")
        target_role = st.selectbox("Target job", sorted(saved_job_profiles))
        uploaded_file = st.file_uploader("Upload CV", type=["pdf", "txt"])
        pasted_cv_text = st.text_area("Or paste CV text", height=260)

    uploaded_cv_text = read_uploaded_cv(uploaded_file)
    cv_text = pasted_cv_text.strip() or uploaded_cv_text.strip()

    if not cv_text:
        st.info("Upload a CV or paste CV text to calculate a job match.")
        return

    st.subheader("CV Text Preview")
    st.text_area("Extracted / pasted CV text", cv_text, height=220)

    if st.button("Calculate Match", type="primary"):
        with st.spinner("Extracting CV skills and calculating target match..."):
            target_job_profile = get_saved_job_profile_by_role(
                target_role,
                DEFAULT_JOB_SKILLS_DIR,
            )
            candidate_profile = extract_candidate_skill_profile(
                cv_text,
                job_profiles=list(saved_job_profiles.values()),
            )
            target_match = calculate_skill_match(candidate_profile, target_job_profile)

        st.session_state["cv_match_candidate_profile"] = candidate_profile.model_dump()
        st.session_state["cv_match_target_match"] = target_match.model_dump()
        st.session_state["cv_match_target_role"] = target_role
        st.session_state.pop("cv_match_all_saved_jobs", None)

    refresh_selected_target_match(target_role)

    if "cv_match_candidate_profile" in st.session_state:
        result = {
            "candidate_profile": st.session_state["cv_match_candidate_profile"],
            "target_job_match": st.session_state["cv_match_target_match"],
        }

        show_candidate_profile(result["candidate_profile"])
        show_target_match(result["target_job_match"])

        if st.button("Show Other Fit"):
            with st.spinner("Calculating match against all saved jobs..."):
                all_saved_job_matches = [
                    match_result.model_dump()
                    for match_result in rank_candidate_against_saved_jobs(
                        st.session_state["cv_match_candidate_profile"],
                        DEFAULT_JOB_SKILLS_DIR,
                    )
                ]

            st.session_state["cv_match_all_saved_jobs"] = all_saved_job_matches

        if "cv_match_all_saved_jobs" in st.session_state:
            st.subheader("Match Against All Saved Jobs")
            match_table = make_match_table(st.session_state["cv_match_all_saved_jobs"])
            st.dataframe(match_table, use_container_width=True, hide_index=True)
            result["all_saved_job_matches"] = st.session_state["cv_match_all_saved_jobs"]

        with st.expander("Full JSON Result"):
            st.json(result)

        st.download_button(
            label="Download Match JSON",
            data=json.dumps(result, indent=4),
            file_name=f"{st.session_state['cv_match_target_role'].lower().replace(' ', '_')}_cv_match.json",
            mime="application/json",
        )


if __name__ == "__main__":
    main()
