from pathlib import Path


def load_job_role_documents(data_dir: str = "data/job_roles") -> dict:
    documents = {}

    for file_path in Path(data_dir).glob("*.txt"):
        role_name = file_path.stem.replace("_", " ").title()

        with open(file_path, "r", encoding="utf-8") as file:
            documents[role_name] = file.read()

    return documents


def retrieve_role_context(target_role: str, documents: dict) -> str:
    for role_name, content in documents.items():
        if target_role.lower() in role_name.lower():
            return content

    return ""