"""Enumerations shared between parts (00-shared §3)."""

from enum import StrEnum


class RoleName(StrEnum):
    """Rows of the `roles` table."""

    ADMIN = "admin"  # accounts, roles, audit; sees no corpus content
    EDITEUR = "editeur"  # the jurist: manages the corpus, sees public + internal
    LECTEUR = "lecteur"  # the citizen: sees public + own uploads


class DocStatus(StrEnum):
    RECEIVED = "received"  # row created, file stored
    EXTRACTING = "extracting"  # P1 extracting / OCR
    CHUNKED = "chunked"  # P1 produced chunks
    INDEXED = "indexed"  # P2 indexed (hidden) + P6 registered
    READY = "ready"  # rights set, searchable
    FAILED = "failed"  # any step failed; document stays hidden


class AuditAction(StrEnum):
    """Values of `audit_log.action`."""

    LOGIN = "login"  # P5, success or not
    QUERY_ASK = "query_ask"  # P5 (log_query), end of every /ask
    ADMIN_UPDATE = "admin_update"  # P5: users, roles, document rights, account requests, web switch
    DOCUMENT_UPLOAD = "document_upload"  # P5, upload accepted
    DOCUMENT_DELETE = "document_delete"  # P5, document deleted
    INGEST_FAILED = "ingest_failed"  # P1, user_id None
    WEB_BLOCKED = "web_blocked"  # P6, query refused by the leak filter (never the query text)


class AccountRequestStatus(StrEnum):
    """Values of `account_requests.status`."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AnswerStatus(StrEnum):
    ANSWERED = "answered"  # answer with verified citations
    UNKNOWN = "unknown"  # nothing found in the documents this user may see
    # (whether the corpus lacks it or it is restricted: never told apart)


class StepType(StrEnum):
    """Process events, P3 (and P4 for `verify`) -> P4 narrator."""

    PLAN = "plan"
    SEARCH = "search"
    GRADE = "grade"
    REFORMULATE = "reformulate"
    WEB = "web"
    WRITE = "write"
    VERIFY = "verify"


# Allowed status transitions (00-shared §3): the pipeline order, any status except ready and
# failed -> failed, failed -> extracting (retry), ready -> indexed (rights change). Anything else
# raises InvalidInput.
ALLOWED_TRANSITIONS: dict[DocStatus, set[DocStatus]] = {
    DocStatus.RECEIVED: {DocStatus.EXTRACTING, DocStatus.FAILED},
    DocStatus.EXTRACTING: {DocStatus.CHUNKED, DocStatus.FAILED},
    DocStatus.CHUNKED: {DocStatus.INDEXED, DocStatus.FAILED},
    DocStatus.INDEXED: {DocStatus.READY, DocStatus.FAILED},
    DocStatus.READY: {DocStatus.INDEXED},  # rights being changed: hidden again
    DocStatus.FAILED: {DocStatus.EXTRACTING},  # retry
}
