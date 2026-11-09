"""Shared errors (00-shared §7).

- The API turns any AppError into {"code": ..., "message": ...} with its http_status, and any other
  exception into 500 {"code": "internal_error"} with no details.
- A document the user may not see is answered with NotFound, never Forbidden.
- Error messages never contain document text, titles of restricted documents, or the question.
"""


class AppError(Exception):
    code: str = "app_error"
    http_status: int = 500

    def __init__(self, message: str = "") -> None:
        super().__init__(message)
        self.message = message


class InvalidInput(AppError):
    code, http_status = "invalid_input", 422


class Unauthenticated(AppError):
    code, http_status = "unauthenticated", 401


class Forbidden(AppError):
    code, http_status = "forbidden", 403


class NotFound(AppError):
    code, http_status = "not_found", 404


class Conflict(AppError):
    code, http_status = "conflict", 409


class LeakBlocked(AppError):
    """Internal to P6, never mapped to HTTP."""

    code, http_status = "leak_blocked", 200

    def __init__(self, message: str = "", hits: int = 0) -> None:
        super().__init__(message)
        self.hits = hits


class TooManyRequests(AppError):
    code, http_status = "too_many_requests", 429


class ServiceError(AppError):
    code, http_status = "service_error", 503
