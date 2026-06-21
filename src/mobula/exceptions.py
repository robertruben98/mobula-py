"""Exception hierarchy raised by the Mobula client.

All errors raised by this library derive from :class:`MobulaError`, so callers
can catch every library-originated failure with a single ``except`` clause.
"""

from typing import Optional


class MobulaError(Exception):
    """Base class for every error raised by ``mobula-py``."""


class MobulaAPIError(MobulaError):
    """Raised when the Mobula API returns a non-success HTTP status.

    Attributes:
        status_code: The HTTP status code returned by the API, when known.
        response_body: The raw response body, when available, for debugging.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class MobulaAuthError(MobulaAPIError):
    """Raised on authentication failures (HTTP 401/403).

    Usually indicates a missing or invalid ``api_key``.
    """


class MobulaRateLimitError(MobulaAPIError):
    """Raised when the API responds with HTTP 429 (rate limited).

    Attributes:
        retry_after: Seconds to wait before retrying, parsed from the
            ``Retry-After`` response header when present.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        retry_after: Optional[float] = None,
    ) -> None:
        super().__init__(message, status_code=status_code, response_body=response_body)
        self.retry_after = retry_after
