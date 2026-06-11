from unittest import TestCase

from backend.cv.cv_skill_extractor import extract_projects_from_text


class CandidateProjectExtractionTests(TestCase):
    def test_extracts_structured_projects_from_project_section(self):
        cv_text = """
PROJECTS
CV Job Matching Assistant | 2025
Role: Developer
Built a platform to compare CVs with target job roles. https://github.com/example/hireready
- Developed FastAPI APIs and React interfaces using Python.
- Improved skill-matching accuracy by 25%.

Image Classification System
Tech Stack: Python, Computer Vision
- Trained a Computer Vision model using Python.
- Achieved 92% validation accuracy.

EDUCATION
MSc Data Science
"""

        projects = extract_projects_from_text(
            cv_text,
            vocabulary=["Python", "FastAPI", "React", "Computer Vision"],
        )

        self.assertEqual(len(projects), 2)
        self.assertEqual(projects[0].name, "CV Job Matching Assistant")
        self.assertEqual(projects[0].role, "Developer")
        self.assertEqual(projects[0].skills, ["FastAPI", "Python", "React"])
        self.assertEqual(projects[0].outcomes, ["Improved skill-matching accuracy by 25%."])
        self.assertEqual(projects[0].links, ["https://github.com/example/hireready"])
        self.assertEqual(projects[1].skills, ["Computer Vision", "Python"])

    def test_does_not_invent_projects_without_project_section(self):
        projects = extract_projects_from_text(
            "EXPERIENCE\nBuilt Project X using Python.",
            vocabulary=["Python"],
        )

        self.assertEqual(projects, [])
