from llama_cpp import Llama
from dotenv import load_dotenv
import json
from pathlib import Path
import os
import re
import time
from string import Template
from pydantic import BaseModel, Field
from typing import List
import yaml

from mistralai.client import Mistral


    # Load .env
load_dotenv()

# Read variables

parent_model_dir = Path(os.getenv("PARENT_MODEL_DIR"))
LOCAL_MISTRAL_MODEL_NAME = os.getenv("LOCAL_MISTRAL_MODEL_NAME")
MISTRAL_API_MODEL_NAME = os.getenv("MISTRAL_API_MODEL_NAME")
OUTPUT_JOB_DESCRIPTION_SKILLS_DIR = Path("CV-job-matching-assistant/data/extracted_skills_"+MISTRAL_API_MODEL_NAME)
SKILL_CATEGORIES_PATH = Path("CV-job-matching-assistant/data/taxonomies/skill_categories.json")
JOB_DESCRIPTION_PROMPTS_PATH = Path("CV-job-matching-assistant/prompts/job_description_data_extractor.yml")

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
    verbatim: str

# class ResponsibilityEvidence(BaseModel):
#     responsibility: str
#     evidence: str


# class ExperienceEvidence(BaseModel):
#     experience: str
#     evidence: str

class JobSkills(BaseModel):

    role: str = ""

    strongly_required_skills: List[SkillEvidence] = Field(default_factory=list)

    required_skills: List[str] = Field(default_factory=list)


    preferred_skills: List[str] = Field(default_factory=list)

    soft_skills: List[str] = Field(default_factory=list)

    tools_and_platforms: List[str] = Field(default_factory=list)

    # experience: List[ExperienceEvidence]

    # responsibilities: List[ResponsibilityEvidence]

    #required_skills: List[str] = Field(default_factory=list)

    #preferred_skills: List[str] = Field(default_factory=list)

    #soft_skills: List[str] = Field(default_factory=list)

    #tools_and_platforms: List[str] = Field(default_factory=list)

    experience: List[str] = Field(default_factory=list)

    responsibilities: List[str] = Field(default_factory=list)


DEFAULT_PROGRAMMING_LANGUAGES = {"python", "java", "javascript", "typescript", "sql"}


def load_programming_languages(path: Path = SKILL_CATEGORIES_PATH) -> set[str]:
    if not path.exists():
        return DEFAULT_PROGRAMMING_LANGUAGES

    try:
        categories = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return DEFAULT_PROGRAMMING_LANGUAGES

    languages = categories.get("programming_languages", [])
    return {language.lower() for language in languages if language}


def load_job_description_prompt(prompt_name: str, job_description: str) -> str:
    prompts = yaml.safe_load(JOB_DESCRIPTION_PROMPTS_PATH.read_text(encoding="utf-8"))
    if prompt_name not in prompts:
        raise KeyError(f"Prompt '{prompt_name}' not found in {JOB_DESCRIPTION_PROMPTS_PATH}")

    return Template(prompts[prompt_name]).substitute(job_description=job_description)


def _is_experience_duration(skill_evidence: SkillEvidence) -> bool:
    text = f"{skill_evidence.skill} {skill_evidence.verbatim}".lower()
    has_years = re.search(r"\b\d+\+?\s*years?\b", text) is not None
    return has_years and "experience" in text

def _extract_skill_from_experience_duration(text: str) -> str | None:
    match = re.search(r"\b(?:with|in)\s+([^,(]+)", text)
    if not match:
        return None

    skill = match.group(1).strip()
    return skill or None


def _append_unique(values: List[str], value: str) -> None:
    if value.lower() not in {existing.lower() for existing in values}:
        values.append(value)


def _unique_clean_strings(values: List[str]) -> List[str]:
    cleaned_values = []
    for value in values:
        cleaned_value = value.strip()
        if cleaned_value:
            _append_unique(cleaned_values, cleaned_value)

    return cleaned_values

def _remove_strongly_required_duplicates(values: List[str], strongly_required_skills: List[SkillEvidence]) -> List[str]:
    strongly_required_names = {skill.skill.lower() for skill in strongly_required_skills}
    return [value for value in values if value.lower() not in strongly_required_names]


def _normalize_required_skill(value: str) -> str:
    value_lower = value.lower()

    if value_lower == "python development":
        return "Python"

    if re.search(r"\b(data ingestion|data processing|data labeling|data curation|data annotation|data preparation)\b", value_lower):
        return "Data preparation and labeling"

    if re.search(r"\b(training|fine-tuning|testing|deploying)\s+machine learning models?\b", value_lower):
        return "Model training and deployment"

    if re.search(r"\bmachine learning model[- ]?(training|deployment|testing|fine-tuning)\b", value_lower):
        return "Model training and deployment"

    if "secure storage" in value_lower and "model training" in value_lower:
        return "ML data management"

    if value_lower.startswith("cloud platforms"):
        return "Cloud platforms"

    return value


def _remove_strongly_required_covered_details(
    values: List[str],
    strongly_required_skills: List[SkillEvidence],
) -> List[str]:
    strongly_required_quotes = [
        skill.verbatim.lower()
        for skill in strongly_required_skills
        if skill.verbatim
    ]

    return [
        value
        for value in values
        if not any(
            value.lower() in quote
            or value.lower().removeprefix("image ") in quote
            for quote in strongly_required_quotes
        )
    ]


def _is_soft_or_workstyle_skill(value: str) -> bool:
    value_lower = value.lower()
    soft_markers = [
        "ownership",
        "collaboration",
        "collaborative",
        "communication",
        "distributed teams",
        "work independently",
        "teamwork",
        "problem-solving",
        "problem solving",
    ]
    return any(marker in value_lower for marker in soft_markers)


def _clean_required_skills(values: List[str], strongly_required_skills: List[SkillEvidence]) -> List[str]:
    normalized_values = [
        _normalize_required_skill(value)
        for value in values
    ]
    unique_values = _unique_clean_strings(normalized_values)
    unique_values = [
        value
        for value in unique_values
        if not _is_soft_or_workstyle_skill(value)
    ]
    unique_values = _remove_strongly_required_duplicates(unique_values, strongly_required_skills)
    return _remove_strongly_required_covered_details(unique_values, strongly_required_skills)


def _is_years_duration_or_seniority(value: str) -> bool:
    value_lower = value.lower()
    return (
        re.search(r"\b\d+\+?\s*(years?|months?)\b", value_lower) is not None
        or any(term in value_lower for term in ["senior", "junior", "mid-level", "lead"])
    )


def _clean_experience(values: List[str], strongly_required_skills: List[SkillEvidence]) -> List[str]:
    strongly_required_quotes = [
        skill.verbatim.lower()
        for skill in strongly_required_skills
        if skill.verbatim
    ]
    cleaned_experience = []

    for value in _unique_clean_strings(values):
        value_lower = value.lower()
        if not _is_years_duration_or_seniority(value):
            continue

        duplicates_strong_requirement = any(
            value_lower in quote or quote in value_lower
            for quote in strongly_required_quotes
        )

        if duplicates_strong_requirement:
            continue

        cleaned_experience.append(value)

    return cleaned_experience


def _clean_tools_and_platforms(values: List[str]) -> List[str]:
    programming_languages = load_programming_languages()

    return [
        value
        for value in _unique_clean_strings(values)
        if value.lower() not in programming_languages
    ]


def _clean_job_skills(data: JobSkills) -> JobSkills:
    cleaned_strongly_required_skills = []

    for skill_evidence in data.strongly_required_skills:
        if _is_experience_duration(skill_evidence):
            _append_unique(data.experience, skill_evidence.verbatim)

            extracted_skill = _extract_skill_from_experience_duration(skill_evidence.verbatim)
            if extracted_skill:
                _append_unique(data.required_skills, extracted_skill)

            continue

        cleaned_strongly_required_skills.append(skill_evidence)

    data.strongly_required_skills = cleaned_strongly_required_skills
    data.required_skills = _clean_required_skills(data.required_skills, data.strongly_required_skills)
    data.preferred_skills = _unique_clean_strings(data.preferred_skills)
    data.soft_skills = _unique_clean_strings(data.soft_skills)
    data.tools_and_platforms = _clean_tools_and_platforms(data.tools_and_platforms)
    data.experience = _clean_experience(data.experience, data.strongly_required_skills)
    data.responsibilities = _unique_clean_strings(data.responsibilities)
    return data

def extract_job_skills(job_description: str) -> dict:
    start_time = time.time()
    client = get_mistral_client()
    prompt = load_job_description_prompt(
        "mistral_api_job_description_extractor",
        job_description
    )

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

    validated_data = _clean_job_skills(JobSkills(**data))

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
    prompt = load_job_description_prompt(
        "mistral_offline_job_description_extractor",
        job_description
    )

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

    data = json.loads(raw_output)
    return _clean_job_skills(JobSkills(**data)).model_dump()


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
