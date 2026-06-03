from __future__ import annotations

import argparse
from pathlib import Path

import fitz

##This will be the content of src/cv_parser.py, which is responsible for extracting text from PDF CVs. The function `extract_text_from_pdf` takes a file path as input and returns the extracted text as a string.
## It only detects keywords and does not perform any analysis or matching. The extracted text can then be passed to other components for further processing, such as skill extraction and job matchin
def extract_text_from_pdf(file_path: str) -> str:
    """Extract plain text from every page of a PDF CV."""
    text = ""

    doc = fitz.open(file_path)

    for page in doc:
        text += page.get_text()

    return text.strip()


def read_cv_text(file_path: str | Path) -> str:
    """Read CV text from either a PDF or plain text file."""
    path = Path(file_path)
    if path.suffix.lower() == ".pdf":
        return extract_text_from_pdf(str(path))

    return path.read_text(encoding="utf-8")


def main() -> None:
    """Run CV text extraction as an individual command-line module."""
    parser = argparse.ArgumentParser(description="Extract text from a CV PDF or TXT file.")
    parser.add_argument("cv_file", help="Path to a PDF or TXT CV file.")
    parser.add_argument("--output", help="Optional path to save extracted text.")
    args = parser.parse_args()

    text = read_cv_text(args.cv_file)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
