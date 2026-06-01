"""Backward-compatible imports for the Mistral API job description cleaner.

Use src.job_description_cleaner_mistral_api for new code.
"""

try:
    from src.job_description_cleaner_mistral_api import *  # noqa: F401,F403
except ModuleNotFoundError as exc:
    if exc.name != "src":
        raise
    from job_description_cleaner_mistral_api import *  # noqa: F401,F403
