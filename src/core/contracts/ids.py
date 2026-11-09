"""Identifiers (00-shared §4). Every part uses these functions; nobody computes an ID another way."""

import hashlib
import uuid

CHUNK_NAMESPACE = uuid.UUID("6f1c2b0e-8a4d-4c1e-9b3a-2d5e7f9a1c30")  # never change


def make_doc_id(file_bytes: bytes, owner_id: uuid.UUID | None) -> str:
    """documents.id. owner_id is set for private uploads, None for corpus documents."""
    scope = str(owner_id) if owner_id else "corpus"
    return hashlib.sha256(scope.encode() + b"\x00" + file_bytes).hexdigest()


def make_file_hash(file_bytes: bytes) -> str:
    """documents.file_hash (kept for reference; the extraction cache is keyed by doc_id)."""
    return hashlib.sha256(file_bytes).hexdigest()


def make_content_hash(normalized_text: str) -> str:
    """Duplicate warning: documents.content_hash. Two files with the same text (e.g. a digital
    PDF and a scan of it) get the same content hash but different doc_ids."""
    return hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()


def make_chunk_id(doc_id: str, chunk_index: int) -> str:
    """Qdrant point ID and BM25 key. chunk_index starts at 0, in document order."""
    return str(uuid.uuid5(CHUNK_NAMESPACE, f"{doc_id}:{chunk_index}"))
