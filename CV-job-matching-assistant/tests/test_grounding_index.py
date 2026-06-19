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

    def test_registry_payload_uses_configuration_and_chunk_ids(self):
        payload = grounding_index._registry_payload(
            [
                {
                    "filename": "notes.txt",
                    "file_hash": "abc123",
                    "chunk_count": 2,
                    "chunk_ids": ["chunk-a", "chunk-b"],
                    "indexed_at": "2026-06-10T13:57:35+00:00",
                }
            ],
            chunk_size=220,
            chunk_overlap=40,
        )

        self.assertEqual(
            payload["configuration"]["embedding_model"],
            "sentence-transformers/all-MiniLM-L6-v2",
        )
        self.assertEqual(payload["configuration"]["embedding_dimensions"], 384)
        self.assertEqual(payload["configuration"]["splitter"], "RecursiveCharacterTextSplitter")
        self.assertEqual(payload["configuration"]["chunk_size"], 220)
        self.assertEqual(payload["configuration"]["chunk_overlap"], 40)
        self.assertEqual(payload["documents"][0]["file_hash"], "abc123")
        self.assertEqual(payload["documents"][0]["chunk_ids"], ["chunk-a", "chunk-b"])
        self.assertIn("updated_at", payload)

    def test_registered_file_hash_supports_old_and_new_registry_keys(self):
        self.assertEqual(grounding_index._registered_file_hash({"file_hash": "new"}), "new")
        self.assertEqual(grounding_index._registered_file_hash({"hash": "old"}), "old")

    def test_unique_chunks_by_id_removes_duplicate_chunk_ids(self):
        class Chunk:
            def __init__(self, chunk_id: str):
                self.metadata = {"chunk_id": chunk_id}
                self.page_content = "same"

        unique = grounding_index._unique_chunks_by_id([Chunk("a"), Chunk("a"), Chunk("b")])

        self.assertEqual([chunk.metadata["chunk_id"] for chunk in unique], ["a", "b"])
