"""Contracts between parts (00-shared §6).

Each Protocol has a fake in fakes/ (written by the part that provides it) and is obtained
through get_<name>() in registry.py (written by P5). Errors refer to errors.py.

Streaming methods are declared `def ... -> AsyncIterator[...]`; implementations write them as
`async def` with `yield`.
"""

from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Protocol
from uuid import UUID

from .models import (
    Answer,
    Chunk,
    DocumentMeta,
    Passage,
    ProcessEvent,
    UserContext,
    WebLookup,
    WebResult,
)

# --- 6.1 Provided by P5 ------------------------------------------------------------------------


class DocumentRights(Protocol):
    def set_document_roles(self, doc_id: str, roles: list[str]) -> dict:
        """hide -> document_roles -> P2 update_roles -> P6 set_blocking -> show -> status ready.
        On any failure: document stays hidden, status failed, log_action, re-raise.
        Errors: NotFound, InvalidInput (unknown role), ServiceError."""
        ...

    def set_status(self, doc_id: str, status: str, error: str | None = None) -> None:
        """The only way to change a document's status. Errors: NotFound, InvalidInput (bad transition)."""
        ...

    def get_status(self, doc_id: str) -> str:
        """Current DocStatus of a document. Errors: NotFound."""
        ...

    def set_content_hash(self, doc_id: str, content_hash: str) -> None:
        """Stores make_content_hash(normalize_ar(full text)), computed by P1 after extraction.
        Errors: NotFound."""
        ...

    def create_document(
        self,
        file_bytes: bytes,
        file_name: str,
        meta: DocumentMeta,
        owner_id: UUID | None,
        uploaded_by: UUID | None,
    ) -> tuple[str, Path]:
        """Computes doc_id, stores the file in storage/uploads/, inserts the documents row
        (status received), logs DOCUMENT_UPLOAD. Returns (doc_id, stored file path).
        Used by POST /documents and by P1's command line. owner_id must be an existing user.
        Errors: Conflict (same doc_id exists), InvalidInput (format, size)."""
        ...


class Audit(Protocol):
    def log_query(self, request_id: UUID, user_id: UUID, query: str, latency_ms: int) -> None:
        """latency_ms: time from the start of the /ask request to the end of its stream,
        stored in audit_log.latency_ms."""
        ...

    def log_action(self, user_id: UUID | None, action_type: str, details: dict) -> None:
        """user_id is None when no user is behind the action: a background job (P1 ingestion,
        publication called from it) or a login with an unknown username.
        audit_log.request_id is filled from the current request's context variable."""
        ...


# --- 6.2 Provided by P1 ------------------------------------------------------------------------


class Ingestion(Protocol):
    def ingest(
        self,
        doc_id: str,
        file_path: Path,
        meta: DocumentMeta,
        roles: list[str],
        owner_id: UUID | None,
    ) -> None:
        """Runs in the background. Extract -> normalize -> chunk -> P2 index -> P6 register ->
        set_status(indexed) -> P5 set_document_roles(doc_id, roles).
        Calls set_status at each step; on failure set_status(failed, error) and stops."""
        ...

    def delete(self, doc_id: str) -> None:
        """Removes chunks from P2, fingerprints from P6, and the cache entry if unused.
        Idempotent: deleting a missing document is not an error."""
        ...


# --- 6.3 Provided by P2 ------------------------------------------------------------------------


class Retrieval(Protocol):
    """update_roles, hide, show and delete change all chunks of the document at once,
    are idempotent, and do nothing (no error) for a doc_id with no chunks. Errors: ServiceError."""

    def index(self, chunks: list[Chunk]) -> None:
        """Embeds and stores chunks, hidden. All chunks belong to one doc_id.
        Re-indexing the same chunk_id overwrites it, and any stored chunk of that doc_id
        with chunk_index >= total_chunks is deleted (left over from an older, longer version)."""
        ...

    def search(self, query: str, ctx: UserContext, top_k: int | None = None) -> list[Passage]:
        """Hybrid search (top_k None means retrieval.top_k_final), filtered BEFORE search by the
        visibility rule:
            not hidden AND (chunk.owner_id == ctx.user_id OR ctx.role in chunk.allowed_roles)
        Errors: InvalidInput if ctx is missing."""
        ...

    def update_roles(self, doc_id: str, roles: list[str]) -> None:
        """Sets allowed_roles on every chunk of the document. Does not change hidden."""
        ...

    def hide(self, doc_id: str) -> None: ...

    def show(self, doc_id: str) -> None: ...

    def delete(self, doc_id: str) -> None: ...


# --- 6.4 Provided by P6 ------------------------------------------------------------------------


class LLMClient(Protocol):
    def chat(
        self,
        messages: list[dict],
        *,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float = 0.0,
    ) -> str: ...

    def stream(
        self, messages: list[dict], *, model: str | None = None, max_tokens: int | None = None
    ) -> AsyncIterator[str]:
        """Async generator of text pieces."""
        ...

    def count_tokens(self, text: str) -> int: ...


class OCRClient(Protocol):
    def ocr_page(self, image: bytes, lang: str = "ar") -> tuple[str, float]:
        """image: an encoded PNG or JPEG file. Returns (text, confidence 0–1)."""
        ...


class LeakIndex(Protocol):
    def register(self, doc_id: str, text: str) -> None:
        """Stores fingerprints; blocking=True until set_blocking says otherwise."""
        ...

    def set_blocking(self, doc_id: str, blocking: bool) -> None: ...

    def delete(self, doc_id: str) -> None: ...


class ModelsClient(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]:
        """bge-m3 vectors (1024 floats each), same order as texts. Errors: ServiceError."""
        ...

    def rerank(self, query: str, texts: list[str]) -> list[float]:
        """Re-ranker scores, same order as texts, higher is better. Errors: ServiceError."""
        ...


class WebSearch(Protocol):
    """Used only inside P6's web agent."""

    def search(
        self, query: str, max_results: int = 5, request_id: UUID | None = None
    ) -> list[WebResult]:
        """Errors: LeakBlocked (carries `hits`) if the query overlaps protected text; ServiceError
        for every other failure (web disabled, timeout, connection error, 5xx)."""
        ...


class WebAgent(Protocol):
    """The only web entry point for other parts (P3)."""

    def lookup(
        self, question: str, ctx: UserContext, language: str, use_web: bool = True
    ) -> WebLookup:
        """Checks the switches (config web.enabled, ctx.web_enabled, use_web), builds a generic
        query from the question only, calls WebSearch.
        Never raises for disabled/blocked/offline: returns status "skipped"."""
        ...


# --- 6.5 Provided by P3 ------------------------------------------------------------------------


class Orchestrator(Protocol):
    def run(self, question: str, ctx: UserContext, use_web: bool = True) -> AsyncIterator[dict]:
        """Async generator of the SSE events of 00-shared §5.7 in order: thinking*, then answer
        or error. The /ask route adds the final `done` event (it measures the latency).
        Passes use_web unchanged to WebAgent.lookup."""
        ...


# --- 6.6 Provided by P4 ------------------------------------------------------------------------


class Writer(Protocol):
    def write(
        self,
        question: str,
        passages: list[Passage],
        web: list[WebResult],
        ctx: UserContext,
        emit: Callable[[ProcessEvent], None] | None = None,
    ) -> Answer:
        """Writes, then verifies with the Juge. Returns status unknown if nothing is supported.
        After the Juge, calls emit(ProcessEvent(step="verify", ...)) if emit is given."""
        ...


class Narrator(Protocol):
    def narrate(self, event: ProcessEvent, language: str) -> AsyncIterator[str]:
        """Async generator of narration text for one process event."""
        ...
