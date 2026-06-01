import json
import streamlit as st

from src.job_description.job_description_cleaner_mistral_api import (
    extract_job_skills,
    save_extracted_skills
)


st.set_page_config(page_title="Job Skill Extractor", layout="wide")

st.title("AI Job Skill Extractor")
st.write("Upload a job description file and generate structured skills JSON.")


uploaded_file = st.file_uploader(
    "Upload job description file",
    type=["txt"]
)


if uploaded_file is not None:
    job_description = uploaded_file.read().decode("utf-8")

    st.subheader("Uploaded Job Description")
    st.text_area("Content", job_description, height=300)

    if st.button("Extract Skills"):
        with st.spinner("Extracting skills using Mistral API..."):
            extracted_data = extract_job_skills(job_description)

        saved_path = save_extracted_skills(extracted_data)

        st.success("Skills extracted successfully!")

        st.subheader("Extracted JSON")
        st.json(extracted_data.model_dump())

        json_string = json.dumps(
            extracted_data.model_dump(),
            indent=4
        )

        st.download_button(
            label="Download JSON",
            data=json_string,
            file_name=saved_path.name,
            mime="application/json"
        )

        st.info(f"File saved locally at: {saved_path.absolute()}")
