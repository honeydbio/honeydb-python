"""Exceptions raised by the HoneyDB API client."""

from __future__ import annotations


class HoneyDBError(Exception):
    """Base class for all HoneyDB API errors.

    Attributes:
        status_code: HTTP status code returned by the API, if available.
        response: The raw text body of the response, if available.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class HoneyDBAuthError(HoneyDBError):
    """Raised on authentication/authorization failures (HTTP 401/403).

    Usually indicates a missing or invalid ``api_id`` / ``api_key``.
    """


class HoneyDBNotFoundError(HoneyDBError):
    """Raised when a requested resource is not found (HTTP 404)."""


class HoneyDBRateLimitError(HoneyDBError):
    """Raised when the API rate/quota limit is exceeded (HTTP 429).

    Attributes:
        retry_after: Seconds to wait before retrying, from the
            ``Retry-After`` header, if provided.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, response=response)
        self.retry_after = retry_after
