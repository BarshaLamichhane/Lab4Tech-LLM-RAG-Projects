from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from backend.interview import grounding_index


class GroundingIndexTests(TestCase):
    def test_upload_and_source_listing_include_hash(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.multiple(
                grounding_index,
                GROUNDING_ROOT=root,
                DOCUMENTS_DIR=root / "documents",
                INDEX_DIR=root / "faiss_index",
                REGISTRY_PATH=root / "registry.json",
            ):
                saved = grounding_index.save_grounding_document("notes.md", b"verified notes")
                sources = grounding_index.list_grounding_sources()

        self.assertEqual(saved["filename"], "notes.md")
        self.assertEqual(sources[0]["hash"], saved["hash"])
        self.assertFalse(sources[0]["indexed"])

    def test_rejects_unsupported_document_type(self):
        with self.assertRaisesRegex(ValueError, "PDF, TXT, MD, or XML"):
            grounding_index.save_grounding_document("notes.exe", b"content")

    def test_use_existing_requires_index(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.multiple(
                grounding_index,
                GROUNDING_ROOT=root,
                DOCUMENTS_DIR=root / "documents",
                INDEX_DIR=root / "faiss_index",
                REGISTRY_PATH=root / "registry.json",
            ):
                with self.assertRaisesRegex(ValueError, "Grounding FAISS index does not exist"):
                    grounding_index.ensure_grounding_index("use_existing")

    def test_duplicate_file_content_is_indexed_once(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.md"
            second = root / "second.md"
            first.write_text("same verified content", encoding="utf-8")
            second.write_text("same verified content", encoding="utf-8")

            unique = grounding_index._unique_documents_by_hash([first, second])

        self.assertEqual(unique, [first])
