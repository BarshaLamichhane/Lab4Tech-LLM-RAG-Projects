from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    from src.cv.cv_parser import read_cv_text
except ModuleNotFoundError:
    from cv.cv_parser import read_cv_text

##This will be the content of src/cv_analyzer.py, which is responsible for analyzing the extracted text from CVs to identify key information such as email addresses and estimate years of experience based on mentioned dates. The main function `analyze_cv` takes the extracted text as input and returns a dictionary containing the email and estimated years of experience.
def extract_email(text):
    """Extract the first email address found in CV text."""
    pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"

    match = re.search(pattern, text)

    return match.group(0) if match else None

def extract_years_experience(text):
    """Estimate experience by counting unique years mentioned in the CV text."""

    years = re.findall(r"\b(20\d{2}|19\d{2})\b", text)
    return len(set(years))


def analyze_cv(text):
    """Return simple CV metadata used by the skill extraction and matching pipeline."""

    return {
        "email": extract_email(text),
        "estimated_experience_years": extract_years_experience(text)
    }


def main() -> None:
    """Run CV metadata analysis as an individual command-line module."""
    parser = argparse.ArgumentParser(description="Analyze CV metadata such as email and estimated years.")
    parser.add_argument("cv_file", help="Path to a PDF or TXT CV file.")
    parser.add_argument("--output", help="Optional path to save JSON analysis.")
    args = parser.parse_args()

    result = analyze_cv(read_cv_text(args.cv_file))
    result_json = json.dumps(result, indent=4)

    if args.output:
        Path(args.output).write_text(result_json, encoding="utf-8")
    else:
        print(result_json)


if __name__ == "__main__":
    main()
