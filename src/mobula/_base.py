"""Shared configuration and response-handling logic for the Mobula clients.

The sync and async clients differ only in how they perform I/O. Everything that
does not touch the network — building request kwargs, constructing headers,
turning an :class:`httpx.Response` into a model or an exception, and computing
backoff delays — lives here so both clients behave identically.
"""

from collections.abc import Mapping
from typing import Any, Optional

import httpx

from mobula.exceptions import MobulaAPIError, MobulaAuthError, MobulaRateLimitError

DEFAULT_BASE_URL = "https://api.mobula.io/api/1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2
DEFAULT_BACKOFF_FACTOR = 0.5


def build_headers(api_key: Optional[str]) -> dict[str, str]:
    """Build the default request headers.

    Mobula authenticates with the raw API key in the ``Authorization`` header
    (no ``Bearer`` prefix). When no key is supplied the header is omitted so
    that the demo/free tier can be exercised.

    Args:
        api_key: The Mobula API key, or ``None`` for unauthenticated use.

    Returns:
        A header dict suitable for the underlying httpx client.
    """
    headers = {
        "Accept": "application/json",
        "User-Agent": "mobula-py",
    }
    if api_key:
        headers["Authorization"] = api_key
    return headers


def clean_params(params: Mapping[str, Any]) -> dict[str, Any]:
    """Drop ``None`` values so optional query parameters are simply omitted."""
    return {key: value for key, value in params.items() if value is not None}


def parse_retry_after(response: httpx.Response) -> Optional[float]:
    """Parse the ``Retry-After`` header into seconds, if present and numeric."""
    raw = response.headers.get("Retry-After")
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def backoff_delay(attempt: int, backoff_factor: float, retry_after: Optional[float]) -> float:
    """Compute how long to sleep before the next retry.

    An explicit ``Retry-After`` from the server wins; otherwise an exponential
    backoff (``backoff_factor * 2**attempt``) is used.

    Args:
        attempt: Zero-based index of the attempt that just failed.
        backoff_factor: Base multiplier for exponential backoff.
        retry_after: Seconds requested by the server, if any.

    Returns:
        The number of seconds to wait.
    """
    if retry_after is not None:
        return retry_after
    return backoff_factor * float(2**attempt)


def handle_response(response: httpx.Response) -> Any:
    """Validate an HTTP response and return its unwrapped JSON payload.

    Mobula wraps successful payloads in a top-level ``data`` key; this returns
    the value of that key (falling back to the whole body if absent).

    Args:
        response: The HTTP response to inspect.

    Returns:
        The unwrapped JSON payload.

    Raises:
        MobulaAuthError: On HTTP 401/403.
        MobulaRateLimitError: On HTTP 429.
        MobulaAPIError: On any other non-2xx status.
    """
    status = response.status_code
    if 200 <= status < 300:
        body = response.json()
        if isinstance(body, dict) and "data" in body:
            return body["data"]
        return body

    body_text = response.text
    if status in (401, 403):
        raise MobulaAuthError(
            f"Authentication failed (HTTP {status}). Check your api_key.",
            status_code=status,
            response_body=body_text,
        )
    if status == 429:
        raise MobulaRateLimitError(
            "Rate limit exceeded (HTTP 429).",
            status_code=status,
            response_body=body_text,
            retry_after=parse_retry_after(response),
        )
    raise MobulaAPIError(
        f"Mobula API returned HTTP {status}.",
        status_code=status,
        response_body=body_text,
    )


def is_retryable(response: httpx.Response) -> bool:
    """Return ``True`` if the response status warrants a retry (429 or 5xx)."""
    return response.status_code == 429 or 500 <= response.status_code < 600


def as_model_list(payload: Any, model: Any) -> list[Any]:
    """Coerce a payload that may be a list (or wrapped) into a list of models."""
    if isinstance(payload, list):
        return [model.model_validate(item) for item in payload]
    return []
