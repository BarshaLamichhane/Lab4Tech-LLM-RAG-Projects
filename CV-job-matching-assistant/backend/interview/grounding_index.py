from __future__ import annotations

import hashlib
import json
import shutil
import ipaddress
import ssl
import socket
import math
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
DEFAULT_CHUNK_SIZE = 900
DEFAULT_CHUNK_OVERLAP = 150
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384
SPLITTER_NAME = "RecursiveCharacterTextSplitter"


def ensure_grounding_index(
    mode: GroundingIndexMode,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> dict:
    chunk_size, chunk_overlap = _validated_chunk_settings(chunk_size, chunk_overlap)
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
    configuration = _registry_configuration(registry)
    chunk_settings_changed = (
        configuration.get("chunk_size") not in {None, chunk_size}
        or configuration.get("chunk_overlap") not in {None, chunk_overlap}
    )

    if mode == "recreate":
        return _recreate_index(documents, current_hashes, mode, chunk_size, chunk_overlap)

    changed = [
        path
        for path in documents
        if path.name in registered and _registered_file_hash(registered[path.name]) != current_hashes[path.name]
    ]
    removed = set(registered) - set(current_hashes)
    if changed or removed or chunk_settings_changed or not _index_exists():
        return _recreate_index(documents, current_hashes, mode, chunk_size, chunk_overlap)

    registered_hashes = {_registered_file_hash(item) for item in registered.values()}
    new_documents = [
        path
        for path in documents
        if path.name not in registered and current_hashes[path.name] not in registered_hashes
    ]
    if not new_documents:
        return {"mode": mode, "sources": list_grounding_sources(), "indexed_chunks": 0}

    chunks = _load_and_chunk(new_documents, chunk_size, chunk_overlap)
    vector_store = _load_vector_store()
    vector_store.add_documents(chunks)
    vector_store.save_local(str(INDEX_DIR))
    new_entries = _registry_entries(new_documents, current_hashes, chunks)
    _save_registry(_registry_payload([*registry.get("documents", []), *new_entries], chunk_size, chunk_overlap))
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
    with urlopen(request, timeout=15, context=_ssl_context()) as response:
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
            "indexed": path.name in indexed and _registered_file_hash(indexed[path.name]) == _file_hash(path),
            "chunk_count": indexed.get(path.name, {}).get("chunk_count", 0),
            "indexed_at": indexed.get(path.name, {}).get("indexed_at"),
        }
        for path in _document_files()
    ]


def list_grounding_index_chunks(limit: int = 100) -> list[dict]:
    if not _index_exists():
        return []
    vector_store = _load_vector_store()
    index_map = getattr(vector_store, "index_to_docstore_id", {}) or {}
    docstore = getattr(getattr(vector_store, "docstore", None), "_dict", {}) or {}
    rows = []
    for index in sorted(index_map)[: max(1, min(limit, 500))]:
        document_id = index_map[index]
        document = docstore.get(document_id)
        if not document:
            continue
        text = document.page_content.strip()
        rows.append(
            {
                "index": index,
                "document_id": document_id,
                "source": document.metadata.get("source", "unknown"),
                "hash": document.metadata.get("hash", ""),
                "chunk_id": document.metadata.get("chunk_id", ""),
                "chunk_preview": text[:700],
                "chunk_length": len(text),
            }
        )
    return rows


def grounding_learning_status() -> dict:
    registry = _load_registry()
    return {
        "has_existing_vector_database": _index_exists(),
        "configuration": _registry_configuration(registry),
        "documents": registry.get("documents", []),
        "updated_at": registry.get("updated_at"),
        "document_directory": str(DOCUMENTS_DIR),
        "index_directory": str(INDEX_DIR),
    }


def grounding_learning_recommendation(chunk_size: int, chunk_overlap: int) -> dict:
    chunk_size, chunk_overlap = _validated_chunk_settings(chunk_size, chunk_overlap)
    documents = _unique_documents_by_hash(_document_files())
    registry = _load_registry()
    configuration = _registry_configuration(registry)
    requested_configuration = _configuration(chunk_size, chunk_overlap)
    registered = {item["filename"]: item for item in registry.get("documents", [])}

    if not _index_exists():
        return {
            "recommended_operation": "recreate",
            "reason": "No existing FAISS index was found under data/grounding/faiss_index.",
            "configuration": requested_configuration,
            "document_count": len(documents),
        }

    changed_fields = [
        key
        for key, value in requested_configuration.items()
        if configuration.get(key) != value
    ]
    if changed_fields:
        return {
            "recommended_operation": "recreate",
            "reason": (
                "Index configuration changed for "
                f"{', '.join(changed_fields)}. Recreate keeps vectors and chunks consistent."
            ),
            "changed_configuration_fields": changed_fields,
            "configuration": requested_configuration,
            "document_count": len(documents),
        }

    current_hashes = {path.name: _file_hash(path) for path in documents}
    known_hashes = {_registered_file_hash(item) for item in registered.values()}
    new_documents = [
        path.name
        for path in documents
        if path.name not in registered and current_hashes[path.name] not in known_hashes
    ]
    changed_documents = [
        path.name
        for path in documents
        if path.name in registered and _registered_file_hash(registered[path.name]) != current_hashes[path.name]
    ]
    removed_documents = [name for name in registered if name not in current_hashes]
    if new_documents or changed_documents or removed_documents:
        return {
            "recommended_operation": "update",
            "reason": "New, changed, or removed grounding documents were detected.",
            "new_documents": new_documents,
            "changed_documents": changed_documents,
            "removed_documents": removed_documents,
            "configuration": requested_configuration,
            "document_count": len(documents),
        }

    return {
        "recommended_operation": "use_existing",
        "reason": "The saved index configuration and grounding document hashes already match.",
        "configuration": requested_configuration,
        "document_count": len(documents),
    }


def build_grounding_learning_index_payload(
    mode: GroundingIndexMode,
    chunk_size: int,
    chunk_overlap: int,
) -> dict:
    operation = ensure_grounding_index(mode, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return inspect_grounding_learning_index(operation)


def inspect_grounding_learning_index(operation: dict | None = None) -> dict:
    if not _index_exists():
        raise ValueError("No grounding FAISS index exists. Choose recreate or update first.")

    vector_store = _load_vector_store()
    registry = _load_registry()
    configuration = _registry_configuration(registry)
    records = _learning_records(vector_store)
    vectors = [record["_vector"] for record in records]
    coordinates = _pca_coordinates(vectors)
    for index, record in enumerate(records):
        record["pca_2d"] = coordinates[index] if index < len(coordinates) else [0.0, 0.0]
        record.pop("_vector", None)

    index = vector_store.index
    return {
        "model": {
            "name": EMBEDDING_MODEL_NAME,
            "type": "Sentence Transformer bi-encoder",
            "base_encoder": "MiniLM transformer",
            "dimensions": getattr(index, "d", EMBEDDING_DIMENSIONS),
            "purpose": "Encode document chunks and user questions into the same semantic vector space.",
        },
        "indexing_steps": [
            "Documents are loaded from data/grounding/documents.",
            "RecursiveCharacterTextSplitter creates overlapping chunks.",
            "HuggingFace sentence-transformer embeddings convert chunks into 384-dimensional vectors.",
            "LangChain stores vectors in FAISS and keeps readable text plus metadata in its docstore.",
            "FAISS index files are saved under data/grounding/faiss_index.",
            "document_registry.json tracks filenames, hashes, chunk IDs, chunk counts, and configuration.",
        ],
        "splitter": {
            "type": SPLITTER_NAME,
            "chunk_size_characters": configuration.get("chunk_size", DEFAULT_CHUNK_SIZE),
            "chunk_overlap_characters": configuration.get("chunk_overlap", DEFAULT_CHUNK_OVERLAP),
            "chunk_count": len(records),
            "separators_tried_in_order": ["\\n\\n", "\\n", " ", ""],
            "how_it_works": (
                "The splitter prefers paragraph breaks, then line breaks, then spaces, "
                "and finally characters when text is still too large."
            ),
        },
        "faiss": {
            "index_class": type(index).__name__,
            "metric_type": _metric_name(index),
            "dimensions": getattr(index, "d", EMBEDDING_DIMENSIONS),
            "total_vectors": getattr(index, "ntotal", len(records)),
            "meaning": "Lower L2 distance means the query vector is closer to a chunk vector.",
        },
        "records": records,
        "saved_files": _learning_saved_files(vector_store),
        "operation": operation or {
            "mode": "use_existing",
            "indexed_chunks": None,
            "sources": list_grounding_sources(),
        },
        "registry": {
            "has_existing_vector_database": _index_exists(),
            **registry,
        },
    }


def search_grounding_learning_context(
    query: str,
    top_k: int = 3,
    maximum_l2_distance: float = 1.2,
) -> dict:
    if not query.strip():
        raise ValueError("Enter a retrieval question.")
    if not _index_exists():
        raise ValueError("No grounding FAISS index exists. Choose recreate or update first.")

    vector_store = _load_vector_store()
    embeddings = _embeddings()
    query_vector = _embed_query(embeddings, query)
    k = min(max(1, top_k), getattr(vector_store.index, "ntotal", top_k))
    distances, positions = vector_store.index.search(_np_array([query_vector]), k)
    nearest_neighbors = []
    for rank, (position, distance) in enumerate(zip(positions[0], distances[0]), start=1):
        if int(position) < 0:
            continue
        document_id = vector_store.index_to_docstore_id[int(position)]
        document = vector_store.docstore.search(document_id)
        chunk_vector = vector_store.index.reconstruct(int(position))
        nearest_neighbors.append(
            {
                "rank": rank,
                "faiss_position": int(position),
                "document_id": document_id,
                "l2_distance": round(float(distance), 6),
                "manual_squared_l2": round(_squared_l2(query_vector, chunk_vector), 6),
                "text": document.page_content,
                "metadata": document.metadata,
                "chunk_vector_first_16": _first_values(chunk_vector, 16),
            }
        )

    relevant = [
        item for item in nearest_neighbors
        if item["l2_distance"] <= maximum_l2_distance
    ]
    return {
        "question": query,
        "tokenization": _tokenize_text(query),
        "query_vector": _vector_details(query_vector),
        "retrieval_steps": [
            "The question is embedded with the same HuggingFace sentence-transformer.",
            "FAISS compares the question vector against stored chunk vectors.",
            "FAISS returns nearest vector positions and squared L2 distances.",
            "LangChain maps positions back to chunk text and metadata.",
            "Only chunks within the distance threshold are treated as context for the LLM.",
        ],
        "maximum_l2_distance": maximum_l2_distance,
        "nearest_neighbors": nearest_neighbors,
        "results": relevant,
        "has_relevant_context": bool(relevant),
        "retrieval_decision": (
            f"Accepted {len(relevant)} chunk(s) with squared L2 distance at or below {maximum_l2_distance}."
            if relevant
            else f"Rejected all nearest chunks because none were within squared L2 distance {maximum_l2_distance}."
        ),
        "safe_answer": (
            "Relevant context was found. The grounded question/evaluation prompt may use it."
            if relevant
            else "I don't know based on the indexed document."
        ),
        "context_for_llm": "\n\n".join(item["text"] for item in relevant),
    }


def _recreate_index(
    documents: list[Path],
    hashes: dict[str, str],
    mode: str,
    chunk_size: int,
    chunk_overlap: int,
) -> dict:
    if INDEX_DIR.exists():
        shutil.rmtree(INDEX_DIR)
    chunks = _load_and_chunk(documents, chunk_size, chunk_overlap)
    if not chunks:
        raise ValueError("Uploaded grounding documents did not contain readable text.")
    vector_store = _faiss_class().from_documents(chunks, _embeddings())
    vector_store.save_local(str(INDEX_DIR))
    _save_registry(_registry_payload(_registry_entries(documents, hashes, chunks), chunk_size, chunk_overlap))
    return {"mode": mode, "sources": list_grounding_sources(), "indexed_chunks": len(chunks)}


def _load_and_chunk(paths: list[Path], chunk_size: int, chunk_overlap: int) -> list:
    Document = _document_class()
    source_documents = [
        Document(page_content=text, metadata={"source": path.name, "hash": _file_hash(path)})
        for path in paths
        if (text := _read_document(path)).strip()
    ]
    splitter = _splitter_class()(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,
    )
    chunks = splitter.split_documents(source_documents)
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = index
        chunk.metadata["chunk_id"] = _chunk_id(chunk)
    return _unique_chunks_by_id(chunks)


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
    chunk_ids: dict[str, list[str]] = {}
    for chunk in chunks:
        source = chunk.metadata.get("source", "unknown")
        chunk_counts[source] = chunk_counts.get(source, 0) + 1
        chunk_ids.setdefault(source, []).append(chunk.metadata.get("chunk_id") or _chunk_id(chunk))
    indexed_at = datetime.now(UTC).isoformat()
    return [
        {
            "filename": path.name,
            "file_hash": hashes[path.name],
            "chunk_count": chunk_counts.get(path.name, 0),
            "chunk_ids": chunk_ids.get(path.name, []),
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


def _chunk_id(chunk) -> str:
    source = str(chunk.metadata.get("source", "unknown"))
    file_hash = str(chunk.metadata.get("hash", ""))
    chunk_index = str(chunk.metadata.get("chunk_index", ""))
    text = chunk.page_content.strip()
    return hashlib.sha256(f"{source}|{file_hash}|{chunk_index}|{text}".encode("utf-8")).hexdigest()


def _unique_chunks_by_id(chunks: list) -> list:
    unique = []
    seen_ids = set()
    for chunk in chunks:
        chunk_id = chunk.metadata.get("chunk_id") or _chunk_id(chunk)
        if chunk_id in seen_ids:
            continue
        seen_ids.add(chunk_id)
        unique.append(chunk)
    return unique


def _registry_payload(documents: list[dict], chunk_size: int, chunk_overlap: int) -> dict:
    now = datetime.now(UTC).isoformat()
    return {
        "configuration": _configuration(chunk_size, chunk_overlap),
        "documents": documents,
        "updated_at": now,
    }


def _configuration(chunk_size: int, chunk_overlap: int) -> dict:
    return {
        "embedding_model": EMBEDDING_MODEL_NAME,
        "embedding_dimensions": EMBEDDING_DIMENSIONS,
        "splitter": SPLITTER_NAME,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
    }


def _registry_configuration(registry: dict) -> dict:
    configuration = registry.get("configuration")
    if isinstance(configuration, dict):
        return configuration
    return {
        "embedding_model": EMBEDDING_MODEL_NAME,
        "embedding_dimensions": EMBEDDING_DIMENSIONS,
        "splitter": SPLITTER_NAME,
        "chunk_size": registry.get("chunk_size"),
        "chunk_overlap": registry.get("chunk_overlap"),
    }


def _registered_file_hash(entry: dict) -> str:
    return str(entry.get("file_hash") or entry.get("hash") or "")


def _load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        return _registry_payload([], DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP)
    return json.loads(REGISTRY_PATH.read_text("utf-8"))


def _save_registry(registry: dict) -> None:
    GROUNDING_ROOT.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def _validated_chunk_settings(chunk_size: int, chunk_overlap: int) -> tuple[int, int]:
    chunk_size = max(200, min(int(chunk_size or DEFAULT_CHUNK_SIZE), 4000))
    chunk_overlap = max(0, min(int(chunk_overlap or DEFAULT_CHUNK_OVERLAP), 1000))
    if chunk_overlap >= chunk_size:
        chunk_overlap = max(0, chunk_size // 5)
    return chunk_size, chunk_overlap


def _ssl_context():
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ModuleNotFoundError:
        return ssl.create_default_context()


def _embeddings():
    from langchain_community.embeddings import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)


def _faiss_class():
    from langchain_community.vectorstores import FAISS

    return FAISS


def _document_class():
    from langchain_core.documents import Document

    return Document


def _splitter_class():
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    return RecursiveCharacterTextSplitter


def _learning_records(vector_store) -> list[dict]:
    index_map = getattr(vector_store, "index_to_docstore_id", {}) or {}
    records = []
    previous_text = ""
    for faiss_position in sorted(index_map):
        document_id = index_map[faiss_position]
        document = vector_store.docstore.search(document_id)
        if not document:
            continue
        vector = vector_store.index.reconstruct(int(faiss_position))
        text = document.page_content
        start_index = int(document.metadata.get("start_index") or 0)
        overlap_text = _longest_overlap(previous_text, text)
        records.append(
            {
                "faiss_position": int(faiss_position),
                "document_id": document_id,
                "text": text,
                "metadata": document.metadata,
                "chunking": {
                    "start_character": start_index,
                    "end_character": start_index + len(text) - 1,
                    "character_count": len(text),
                    "overlap_text": overlap_text,
                    "overlap_character_count": len(overlap_text),
                },
                "tokenization": _tokenize_text(text),
                "vector": _vector_details(vector),
                "_vector": vector,
            }
        )
        previous_text = text
    return records


def _learning_saved_files(vector_store) -> dict:
    faiss_path = INDEX_DIR / "index.faiss"
    pickle_path = INDEX_DIR / "index.pkl"
    registry = _load_registry()
    vector_samples = []
    for position in range(min(getattr(vector_store.index, "ntotal", 0), 3)):
        vector_samples.append(
            {
                "faiss_position": position,
                "first_12_values": _first_values(vector_store.index.reconstruct(position), 12),
            }
        )
    index_map = getattr(vector_store, "index_to_docstore_id", {}) or {}
    docstore = getattr(getattr(vector_store, "docstore", None), "_dict", {}) or {}
    document_samples = [
        {
            "document_id": document_id,
            "faiss_position": next(
                (
                    position
                    for position, mapped_id in index_map.items()
                    if mapped_id == document_id
                ),
                None,
            ),
            "text": document.page_content,
            "metadata": document.metadata,
        }
        for document_id, document in docstore.items()
    ]
    return {
        "index_faiss": {
            "path": str(faiss_path),
            "size_bytes": faiss_path.stat().st_size if faiss_path.exists() else 0,
            "stores": "Binary FAISS index containing numeric vectors and nearest-neighbor structure.",
            "does_not_store": "Readable chunk text or metadata.",
            "details": {
                "index_class": type(vector_store.index).__name__,
                "metric_type": _metric_name(vector_store.index),
                "dimensions_per_vector": getattr(vector_store.index, "d", EMBEDDING_DIMENSIONS),
                "total_vectors": getattr(vector_store.index, "ntotal", 0),
                "sample_vectors": vector_samples,
            },
        },
        "index_pkl": {
            "path": str(pickle_path),
            "size_bytes": pickle_path.stat().st_size if pickle_path.exists() else 0,
            "stores": "LangChain docstore with readable chunk text, metadata, and FAISS-position mapping.",
            "security_note": "Only load pickle files from trusted sources.",
            "details": {
                "document_count": len(docstore),
                "mapping_count": len(index_map),
                "index_to_docstore_id": index_map,
                "documents": document_samples,
            },
        },
        "registry_json": {
            "path": str(REGISTRY_PATH),
            "size_bytes": REGISTRY_PATH.stat().st_size if REGISTRY_PATH.exists() else 0,
            "stores": "Document filenames, hashes, chunk IDs, chunk counts, timestamps, and index configuration.",
            "details": registry,
        },
    }


def _tokenize_text(text: str) -> dict:
    try:
        client = getattr(_embeddings(), "client", None) or getattr(_embeddings(), "_client", None)
        tokenizer = getattr(client, "tokenizer", None)
        if tokenizer is None:
            return _fallback_tokenization(text)
        encoded = tokenizer(
            text,
            add_special_tokens=True,
            truncation=True,
            return_attention_mask=True,
        )
        return {
            "tokens": tokenizer.convert_ids_to_tokens(encoded["input_ids"]),
            "token_ids": encoded["input_ids"],
            "attention_mask": encoded["attention_mask"],
        }
    except Exception:
        return _fallback_tokenization(text)


def _fallback_tokenization(text: str) -> dict:
    tokens = text.split()
    return {
        "tokens": tokens[:120],
        "token_ids": list(range(min(len(tokens), 120))),
        "attention_mask": [1] * min(len(tokens), 120),
    }


def _embed_query(embeddings, query: str):
    return embeddings.embed_query(query)


def _vector_details(vector) -> dict:
    values = [float(value) for value in vector]
    if not values:
        return {
            "dimensions": 0,
            "first_16_values": [],
            "minimum": 0,
            "maximum": 0,
            "mean": 0,
            "magnitude": 0,
            "non_zero_values": 0,
        }
    magnitude = math.sqrt(sum(value * value for value in values))
    return {
        "dimensions": len(values),
        "first_16_values": [round(value, 5) for value in values[:16]],
        "minimum": round(min(values), 6),
        "maximum": round(max(values), 6),
        "mean": round(sum(values) / len(values), 6),
        "magnitude": round(magnitude, 6),
        "non_zero_values": sum(1 for value in values if value != 0),
    }


def _first_values(vector, count: int) -> list[float]:
    return [round(float(value), 6) for value in list(vector)[:count]]


def _squared_l2(left, right) -> float:
    return sum((float(a) - float(b)) ** 2 for a, b in zip(left, right))


def _np_array(values):
    import numpy as np

    return np.array(values, dtype=np.float32)


def _pca_coordinates(vectors: list) -> list[list[float]]:
    if not vectors:
        return []
    if len(vectors) == 1:
        return [[0.0, 0.0]]
    import numpy as np

    matrix = np.array(vectors, dtype=np.float32)
    centered = matrix - matrix.mean(axis=0)
    _, _, components = np.linalg.svd(centered, full_matrices=False)
    dimensions = min(2, components.shape[0])
    projected = centered @ components[:dimensions].T
    if dimensions == 1:
        projected = np.column_stack([projected[:, 0], np.zeros(len(vectors))])
    return projected.round(5).tolist()


def _longest_overlap(previous: str, current: str) -> str:
    max_length = min(len(previous), len(current))
    for length in range(max_length, 0, -1):
        if previous[-length:] == current[:length]:
            return current[:length]
    return ""


def _metric_name(index) -> str:
    try:
        import faiss

        if getattr(index, "metric_type", None) == faiss.METRIC_L2:
            return "L2 distance"
        if getattr(index, "metric_type", None) == faiss.METRIC_INNER_PRODUCT:
            return "Inner product"
    except Exception:
        pass
    return str(getattr(index, "metric_type", "unknown"))
