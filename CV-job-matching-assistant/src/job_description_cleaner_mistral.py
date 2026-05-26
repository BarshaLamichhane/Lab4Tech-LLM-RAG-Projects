from llama_cpp import Llama
from dotenv import load_dotenv
import json
from pathlib import Path
import os
import time


    # Load .env
load_dotenv()


# Read variables

parent_model_dir = Path(os.getenv("PARENT_MODEL_DIR"))
model_name = os.getenv("MISTRAL_MODEL_NAME")

OUTPUT_JOB_DESCRIPTION_SKILLS_DIR = Path("CV-job-matching-assistant/data/extracted_skills_"+model_name)

def load_llm():
    parent_model_dir = Path(os.getenv("PARENT_MODEL_DIR"))
    model_name = os.getenv("MISTRAL_MODEL_NAME")
    return Llama(
        model_path=os.path.join(parent_model_dir, model_name),
        n_ctx=4096,
        n_threads=8,
        verbose=False
    )


def extract_job_skills(job_description: str, llm) -> dict:
    start_time = time.time()
    prompt = f"""
    You are an expert job description parser.


    Return ONLY valid JSON in this format:

    {{
    "role": "",
    "required_skills": [],
    "preferred_skills": [],
    "soft_skills": [],
    "tools_and_platforms": [],
    "experience": [],
    "responsibilities": []
    }}

    Rules:
    - Use only information explicitly present in the job description.
    - Do not invent skills.
    - Keep skill names concise and standardized.
    - Ignore salary, location, benefits, and company marketing text.
    - Return JSON only.

    Job description:
    \"\"\"
    {job_description}
    \"\"\"
    """

    response = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": "You extract structured JSON from job descriptions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=1200,
        response_format={"type": "json_object"}
    )

    raw_output = response["choices"][0]["message"]["content"]
    end_time = time.time()
    print(f"LLM response time for extracting job description skills: {end_time - start_time:.2f} seconds")

    return json.loads(raw_output)


def save_extracted_skills(data: dict, output_dir: Path = OUTPUT_JOB_DESCRIPTION_SKILLS_DIR):
    start_time = time.time()
    #output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    role = data.get("role", "unknown_role")
    file_name = role.lower().replace(" ", "_") + "_skills.json"

    output_path = output_dir / file_name

    print(f"Saving extracted skills to: {output_path}")
    
    output_path.write_text(
        json.dumps(data, indent=4),
        encoding="utf-8"
    )
    print(f"Saving extracted skills to: {output_path}")
    end_time = time.time()
    print(f"Time taken to save extracted skillss: {end_time - start_time:.2f} seconds")
    
    return output_path
