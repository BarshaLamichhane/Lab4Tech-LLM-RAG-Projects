import re

##This will be the content of src/cv_analyzer.py, which is responsible for analyzing the extracted text from CVs to identify key information such as email addresses and estimate years of experience based on mentioned dates. The main function `analyze_cv` takes the extracted text as input and returns a dictionary containing the email and estimated years of experience.
def extract_email(text):
    pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"

    match = re.search(pattern, text)

    return match.group(0) if match else None


def extract_years_experience(text):

    years = re.findall(r"\b(20\d{2}|19\d{2})\b", text)

    return len(set(years))


def analyze_cv(text):

    return {
        "email": extract_email(text),
        "estimated_experience_years": extract_years_experience(text)
    }