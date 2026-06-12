from __future__ import annotations

import hashlib
import json
import shutil
import ipaddress
import socket
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from backend.cv.cv_parser import extract_text_from_pdf


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GROUNDING_ROOT = PROJECT_ROOT / "data" / "grounding"
DOCUMENTS_DIR = GROUNDING_ROOT / "documents"
INDEX_DIR = GROUNDING_ROOT / "faiss_index"
REGISTRY_PATH = GROUNDING_ROOT / "document_registry.json"
SUPPORTED_SUFFIXES = {".pdf", ".txt", ".md", ".xml"}
GroundingIndexMode = Literal["use_existing", "recreate", "update"]


def ensure_grounding_index(mode: GroundingIndexMode) -> dict:
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    if mode == "use_existing":
        if not _index_exists():
            raise ValueError("Grounding FAISS index does not exist. Choose recreate or update.")
        return {"mode": mode, "sources": list_grounding_sources(), "indexed_chunks": None}

    documents = _unique_documents_by_hash(_document_files())
    if not documents:
        raise ValueError("Grounded material selected, but no verified documents are uploaded.")

    current_hashes = {path.name: _file_hash(path) for path in documents}
    registry = _load_registry()
    registered = {item["filename"]: item for item in registry.get("documents", [])}

    if mode == "recreate":
        return _recreate_index(documents, current_hashes, mode)

    changed = [
        path
        for path in documents
        if path.name in registered and registered[path.name]["hash"] != current_hashes[path.name]
    ]
    removed = set(registered) - set(current_hashes)
    if changed or removed or not _index_exists():
        return _recreate_index(documents, current_hashes, mode)

    registered_hashes = {item["hash"] for item in registered.values()}
    new_documents = [
        path
        for path in documents
        if path.name not in registered and current_hashes[path.name] not in registered_hashes
    ]
    if not new_documents:
        return {"mode": mode, "sources": list_grounding_sources(), "indexed_chunks": 0}

    chunks = _load_and_chunk(new_documents)
    vector_store = _load_vector_store()
    vector_store.add_documents(chunks)
    vector_store.save_local(str(INDEX_DIR))
    new_entries = _registry_entries(new_documents, current_hashes, chunks)
    _save_registry({"documents": [*registry.get("documents", []), *new_entries]})
    return {"mode": mode, "sources": list_grounding_sources(), "indexed_chunks": len(chunks)}


def retrieve_grounding_context(query: str, top_k: int = 5) -> list[dict]:
    if not query.strip():
        return []
    if not _index_exists():
        raise ValueError("Grounding FAISS index does not exist. Choose recreate or update.")
    documents = _load_vector_store().similarity_search(query, k=max(1, min(top_k, 20)))
    return [
        {
            "source": document.metadata.get("source", "unknown"),
            "text": document.page_content,
        }
        for document in documents
        if document.page_content.strip()
    ]


def save_grounding_document(filename: str, content: bytes) -> dict:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError("Grounding documents must be PDF, TXT, MD, or XML files.")
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(filename).name
    path = DOCUMENTS_DIR / safe_name
    path.write_bytes(content)
    return {"filename": safe_name, "size": len(content), "hash": _file_hash(path)}


def save_grounding_url(url: str, filename: str | None = None, max_bytes: int = 10_000_000) -> dict:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Online grounding material must use a valid HTTPS URL.")
    for address in socket.getaddrinfo(parsed.hostname, 443):
        ip = ipaddress.ip_address(address[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise ValueError("Private or local URLs are not allowed.")
    request = Request(url, headers={"User-Agent": "HireReadyAI/1.0"})
    with urlopen(request, timeout=15) as response:
        content = response.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise ValueError("Online grounding material exceeds the upload size limit.")
    inferred_name = filename or Path(parsed.path).name or f"{parsed.hostname}.txt"
    if Path(inferred_name).suffix.lower() not in SUPPORTED_SUFFIXES:
        inferred_name = f"{Path(inferred_name).stem or parsed.hostname}.txt"
    return save_grounding_document(inferred_name, content)


def list_grounding_sources() -> list[dict]:
    registry = _load_registry()
    indexed = {item["filename"]: item for item in registry.get("documents", [])}
    return [
        {
            "filename": path.name,
            "size": path.stat().st_size,
            "hash": _file_hash(path),
            "indexed": path.name in indexed and indexed[path.name]["hash"] == _file_hash(path),
            "chunk_count": indexed.get(path.name, {}).get("chunk_count", 0),
            "indexed_at": indexed.get(path.name, {}).get("indexed_at"),
        }
        for path in _document_files()
    ]


def _recreate_index(documents: list[Path], hashes: dict[str, str], mode: str) -> dict:
    if INDEX_DIR.exists():
        shutil.rmtree(INDEX_DIR)
    chunks = _load_and_chunk(documents)
    if not chunks:
        raise ValueError("Uploaded grounding documents did not contain readable text.")
    vector_store = _faiss_class().from_documents(chunks, _embeddings())
    vector_store.save_local(str(INDEX_DIR))
    _save_registry({"documents": _registry_entries(documents, hashes, chunks)})
    return {"mode": mode, "sources": list_grounding_sources(), "indexed_chunks": len(chunks)}


def _load_and_chunk(paths: list[Path]) -> list:
    Document = _document_class()
    source_documents = [
        Document(page_content=text, metadata={"source": path.name, "hash": _file_hash(path)})
        for path in paths
        if (text := _read_document(path)).strip()
    ]
    splitter = _splitter_class()(chunk_size=900, chunk_overlap=150)
    return splitter.split_documents(source_documents)


def _read_document(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        return extract_text_from_pdf(str(path))
    if path.suffix.lower() == ".xml":
        from xml.etree import ElementTree

        root = ElementTree.parse(path).getroot()
        return " ".join(text.strip() for text in root.itertext() if text.strip())
    return path.read_text("utf-8", errors="ignore")


def _registry_entries(paths: list[Path], hashes: dict[str, str], chunks: list) -> list[dict]:
    chunk_counts: dict[str, int] = {}
    for chunk in chunks:
        source = chunk.metadata.get("source", "unknown")
        chunk_counts[source] = chunk_counts.get(source, 0) + 1
    indexed_at = datetime.now(UTC).isoformat()
    return [
        {
            "filename": path.name,
            "hash": hashes[path.name],
            "chunk_count": chunk_counts.get(path.name, 0),
            "indexed_at": indexed_at,
        }
        for path in paths
    ]


def _load_vector_store():
    return _faiss_class().load_local(
        str(INDEX_DIR),
        _embeddings(),
        allow_dangerous_deserialization=True,
    )


def _document_files() -> list[Path]:
    if not DOCUMENTS_DIR.exists():
        return []
    return sorted(
        path for path in DOCUMENTS_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )


def _unique_documents_by_hash(paths: list[Path]) -> list[Path]:
    unique = []
    seen_hashes = set()
    for path in paths:
        digest = _file_hash(path)
        if digest not in seen_hashes:
            seen_hashes.add(digest)
            unique.append(path)
    return unique


def _index_exists() -> bool:
    return (INDEX_DIR / "index.faiss").exists() and (INDEX_DIR / "index.pkl").exists()


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        return {"documents": []}
    return json.loads(REGISTRY_PATH.read_text("utf-8"))


def _save_registry(registry: dict) -> None:
    GROUNDING_ROOT.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def _embeddings():
    from langchain_community.embeddings import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def _faiss_class():
    from langchain_community.vectorstores import FAISS

    return FAISS


def _document_class():
    from langchain_core.documents import Document

    return Document


def _splitter_class():
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    return RecursiveCharacterTextSplitter
