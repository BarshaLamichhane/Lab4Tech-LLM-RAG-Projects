from pathlib import Path
import json
import os

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()


INPUT_DIR = Path("data/job_roles/raw_job_postings")
OUTPUT_DIR = Path("data/job_roles/cleaned_job_postings")

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


JOB_SCHEMA = {
    "type": "object",
    "properties": {
        "role": {"type": "string"},
        "required_skills": {
            "type": "array",
            "items": {"type": "string"}
        },
        "preferred_skills": {
            "type": "array",
            "items": {"type": "string"}
        },
        "soft_skills": {
            "type": "array",
            "items": {"type": "string"}
        },
        "tools_and_platforms": {
            "type": "array",
            "items": {"type": "string"}
        },
        "experience": {
            "type": "array",
            "items": {"type": "string"}
        },
        "responsibilities": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": [
        "role",
        "required_skills",
        "preferred_skills",
        "soft_skills",
        "tools_and_platforms",
        "experience",
        "responsibilities"
    ]
}


def build_prompt(job_text: str) -> str:
    return f"""
You are an expert job description parser.

Extract structured information from the job post.

Rules:
- Do not invent skills.
- Use only information present in the job post.
- Keep skill names short and clean.
- Separate required skills, preferred skills, soft skills, tools, experience, and responsibilities.
- Ignore benefits, company marketing text, and application instructions.

Job post:
\"\"\"
{job_text}
\"\"\"
"""


def extract_with_gemini(job_text: str) -> dict:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=build_prompt(job_text),
        config=types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
            response_schema=JOB_SCHEMA,
        ),
    )

    return json.loads(response.text)


def process_single_file(file_path: Path) -> None:
    job_text = file_path.read_text(encoding="utf-8")

    extracted_data = extract_with_gemini(job_text)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_DIR / f"{file_path.stem}_skills.json"

    output_path.write_text(
        json.dumps(extracted_data, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"Processed: {file_path.name}")
    print(f"Saved: {output_path}")


def process_all_job_posts() -> None:
    txt_files = list(INPUT_DIR.glob("*.txt"))
    print(f"Found {len(txt_files)} job posts to process in {INPUT_DIR}")

    if not txt_files:
        print("No .txt job posts found in data/job_posts/")
        return

    for file_path in txt_files:
        process_single_file(file_path)


def job_description_cleaner_main():
    process_all_job_posts()