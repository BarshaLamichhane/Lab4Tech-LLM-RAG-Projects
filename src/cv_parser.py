import fitz

##This will be the content of src/cv_parser.py, which is responsible for extracting text from PDF CVs. The function `extract_text_from_pdf` takes a file path as input and returns the extracted text as a string.
## It only detects keywords and does not perform any analysis or matching. The extracted text can then be passed to other components for further processing, such as skill extraction and job matchin
def extract_text_from_pdf(file_path: str) -> str:
    text = ""

    doc = fitz.open(file_path)

    for page in doc:
        text += page.get_text()

    return text.strip()
