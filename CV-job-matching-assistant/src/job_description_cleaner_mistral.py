from llama_cpp import Llama
from dotenv import load_dotenv
import json
from pathlib import Path
import os
import time
from pydantic import BaseModel, Field
from typing import List

from mistralai.client import Mistral


    # Load .env
load_dotenv()

# Read variables

parent_model_dir = Path(os.getenv("PARENT_MODEL_DIR"))
LOCAL_MISTRAL_MODEL_NAME = os.getenv("LOCAL_MISTRAL_MODEL_NAME")
MISTRAL_API_MODEL_NAME = os.getenv("MISTRAL_API_MODEL_NAME")
OUTPUT_JOB_DESCRIPTION_SKILLS_DIR = Path("CV-job-matching-assistant/data/extracted_skills_"+MISTRAL_API_MODEL_NAME)

def get_mistral_client() -> Mistral:
    api_key = os.getenv("MISTRAL_API_KEY")

    if not api_key:
        raise ValueError("MISTRAL_API_KEY not found in .env file")

    return Mistral(api_key=api_key)


def load_llm():
    parent_model_dir = Path(os.getenv("PARENT_MODEL_DIR"))
    model_name = os.getenv("LOCAL_MISTRAL_MODEL_NAME")
    return Llama(
        model_path=os.path.join(parent_model_dir, model_name),
        n_ctx=4096,
        n_threads=8,
        verbose=False
    )
# =========================
# PYDANTIC SCHEMA
# =========================
class SkillEvidence(BaseModel):
    skill: str
    evidence: str

class ResponsibilityEvidence(BaseModel):
    responsibility: str
    evidence: str


class ExperienceEvidence(BaseModel):
    experience: str
    evidence: str

class JobSkills(BaseModel):

    role: str = ""

    required_skills: List[SkillEvidence]

    preferred_skills: List[SkillEvidence]

    soft_skills: List[SkillEvidence]

    tools_and_platforms: List[SkillEvidence]

    experience: List[ExperienceEvidence]

    responsibilities: List[ResponsibilityEvidence]

    #required_skills: List[str] = Field(default_factory=list)

    #preferred_skills: List[str] = Field(default_factory=list)

    #soft_skills: List[str] = Field(default_factory=list)

    #tools_and_platforms: List[str] = Field(default_factory=list)

    #experience: List[str] = Field(default_factory=list)

    #responsibilities: List[str] = Field(default_factory=list)

def extract_job_skills(job_description: str) -> dict:
    start_time = time.time()
    client = get_mistral_client()
    prompt = f"""
    You are an expert job description parser with a precision focus on extracting structured skills information.
    

    

    Return ONLY valid JSON. 

    STRICT JSON SCHEMA:

    {{
        "role": "string",

        "required_skills": [
            {{
            "skill": "string",
            "evidence": "exact verbatim quote from job description"
            }}
        ],

        "preferred_skills": [
            {{
            "skill": "string",
            "evidence": "exact verbatim quote from job description"
            }}
        ],

        "soft_skills": [
            {{
            "skill": "string",
            "evidence": "exact verbatim quote from job description"
            }}
        ],

        "tools_and_platforms": [
            {{
            "skill": "string",
            "evidence": "exact verbatim quote from job description"
            }}
        ],

        "experience": [
            {{
            "experience": "string",
            "evidence": "exact verbatim quote from job description"
            }}
        ],

        "responsibilities": [
            {{
            "responsibility": "string",
            "evidence": "exact verbatim quote from job description"
            }}
        ]
    }}
    

    Rules:
    
    - Extract only information explicitly written in the job description.
    - Do not invent skills.
    - Keep skill names concise and standardized.
    - Ignore salary, location, benefits, and company marketing text.
    - Return JSON only.
    - include the exact verbatim sentence or phrase from the job description
    - do not paraphrase the evidence - it must be a direct quote that supports why you classified a skill as required, preferred, soft skill, tool/platform, experience, or responsibility.
   

    Job description:
    \"\"\"
    {job_description}
    \"\"\"
    """

    response = client.chat.complete(
        model=MISTRAL_API_MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You extract structured JSON from job descriptions."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    raw_output = response.choices[0].message.content
    data = json.loads(raw_output)

    validated_data = JobSkills(**data)

    end_time = time.time()
    print(f"Mistral API extraction time: {end_time - start_time:.2f} seconds")
    return validated_data

def save_extracted_skills(data: JobSkills, output_dir: Path = OUTPUT_JOB_DESCRIPTION_SKILLS_DIR) -> Path:
    start_time = time.time()
    #output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    #role = data.get("role", "unknown_role")
    role = data.role or "unknown_role"
    file_name = role.lower().replace(" ", "_") + "_skills.json"

    output_path = output_dir / file_name

    print(f"Saving extracted skills to: {output_path}")
    
    output_path.write_text(
        json.dumps(data.model_dump(), indent=4),
        encoding="utf-8"
    )
    print(f"Saving extracted skills to: {output_path}")
    end_time = time.time()
    print(f"Time taken to save extracted skillss: {end_time - start_time:.2f} seconds")
    
    return output_path

  
def extract_job_skills_with_offline_mistral_model(job_description: str, llm) -> dict:
    start_time = time.time()
    prompt = f"""
    You are an expert job description parser with a precision focus on extracting structured skills information.
    


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
    - Extract only information explicitly written in the job description.
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


def save_extracted_skills_from_offline_mistral_model(data: dict, output_dir: Path = OUTPUT_JOB_DESCRIPTION_SKILLS_DIR):
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
