import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from backend.interview.preparation_interview import _build_prompt
from backend.job_description.job_description_cleaner_mistral_api import JobSkills, save_extracted_skills
from backend.job_description.job_profile_catalog import profile_paths
from backend.matching.skill_matching_engine import load_saved_job_profiles


class JobProfileCompanyContextTests(TestCase):
    def test_saved_profile_uses_company_filename_and_updates_catalog(self):
        with TemporaryDirectory() as directory:
            output_dir = Path(directory)
            path = save_extracted_skills(
                JobSkills(
                    role="Data Engineer",
                    company_name="MeteoSwiss",
                    company_context="Weather forecasting and climate data services",
                ),
                output_dir,
            )
            catalog = json.loads((output_dir / "index.json").read_text(encoding="utf-8"))

        self.assertRegex(path.name, r"data_engineer_meteoswiss_\d{4}\.json")
        self.assertEqual(catalog["profiles"][0]["company"], "MeteoSwiss")
        self.assertEqual(catalog["profiles"][0]["file"], path.name)

    def test_catalog_is_not_loaded_as_a_job_profile(self):
        with TemporaryDirectory() as directory:
            output_dir = Path(directory)
            (output_dir / "index.json").write_text('{"profiles": []}', encoding="utf-8")
            (output_dir / "ai_engineer.json").write_text(
                '{"role": "AI Engineer", "required_skills": ["Python"]}',
                encoding="utf-8",
            )

            paths = profile_paths(output_dir)
            profiles = load_saved_job_profiles(output_dir)

        self.assertEqual([path.name for path in paths], ["ai_engineer.json"])
        self.assertIn("AI Engineer", profiles)

    def test_company_context_is_added_only_when_enabled(self):
        context = {
            "company_name": "MeteoSwiss",
            "company_context": "Weather forecasting and climate data services",
            "industry_domain": "Weather and climate",
        }
        normal_prompt = _build_prompt(
            role="Python Engineer",
            selected_skills=["Python"],
            question_count=1,
            level="intermediate",
            interview_type="coding",
            candidate_projects=[],
            existing_questions=[],
            company_context=context,
        )
        company_prompt = _build_prompt(
            role="Python Engineer",
            selected_skills=["Python"],
            question_count=1,
            level="intermediate",
            interview_type="coding",
            candidate_projects=[],
            existing_questions=[],
            use_company_context=True,
            company_context=context,
        )

        self.assertNotIn("MeteoSwiss", normal_prompt)
        self.assertIn("MeteoSwiss", company_prompt)
        self.assertIn("Do not force company context", company_prompt)
