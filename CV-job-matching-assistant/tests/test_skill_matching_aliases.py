from unittest import TestCase

from backend.cv.cv_skill_extractor import extract_skills_from_text, load_skill_categories
from backend.matching.skill_matching_engine import load_skill_categories as load_matching_categories
from backend.matching.skill_matching_engine import skills_match


class SkillMatchingAliasTests(TestCase):
    def setUp(self):
        load_skill_categories.cache_clear()
        load_matching_categories.cache_clear()

    def test_rag_alias_matches_retrieval_augmented_generation(self):
        self.assertTrue(skills_match("RAG architectures", "Retrieval-augmented generation"))
        self.assertTrue(skills_match("RAG", "Retrieval augmented generation"))

    def test_large_scale_dataset_processing_matches_data_preprocessing_requirement(self):
        self.assertTrue(
            skills_match(
                "Large-Scale Dataset Processing",
                "Data preprocessing and large dataset handling",
            )
        )

    def test_large_scale_dataset_processing_is_extracted_from_cv_text(self):
        skills = extract_skills_from_text(
            "Computing: CUDA-aware GPU Training, Multiprocessing, Linux, Bash, Large-Scale Dataset Processing"
        )

        self.assertIn("Data preprocessing and large dataset handling", skills)
