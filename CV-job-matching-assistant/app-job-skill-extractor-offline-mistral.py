import json

import streamlit as st
import time




from src.job_description_cleaner_mistral import (
    load_llm,
    extract_job_skills_with_offline_mistral_model,
    save_extracted_skills_from_offline_mistral_model
)

print("Starting the Job Description Cleaner application...")



# st.set_page_config(page_title="Job Skill Extractor", layout="wide")

# st.title("AI Job Skill Extractor")

# st.write("Upload a job description file and generate structured skills JSON.")


# @st.cache_resource
# def get_llm():
#     return load_llm()

# start_time = time.time()
# llm = get_llm()
# end_time = time.time()
# print(f"LLM loading time in user interface: {end_time - start_time:.2f} seconds")

# uploaded_file = st.file_uploader(
#     "Upload job description file",
#     type=["txt"]
# )


# if uploaded_file is not None:
#     job_description = uploaded_file.read().decode("utf-8")

#     st.subheader("Uploaded Job Description")
#     st.text_area("Content", job_description, height=300)

#     if st.button("Extract Skills"):
#         with st.spinner("Extracting skills..."):
#             extracted_data = extract_job_skills_with_offline_mistral_model(job_description, llm)

#         saved_path = save_extracted_skills_from_offline_mistral_model(extracted_data)

#         st.success("Skills extracted successfully!")

#         st.subheader("Extracted JSON")
#         st.json(extracted_data)

#         json_string = json.dumps(extracted_data, indent=4)

#         st.download_button(
#             label="Download JSON",
#             data=json_string,
#             file_name=saved_path.name,
#             mime="application/json"
#         )

#         st.info(f"File saved locally at: {saved_path}")