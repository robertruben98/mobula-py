"""Tests for the Mobula exception hierarchy."""

import pytest

from mobula import (
    MobulaAPIError,
    MobulaAuthError,
    MobulaError,
    MobulaRateLimitError,
)


def test_all_exceptions_subclass_mobula_error():
    assert issubclass(MobulaAPIError, MobulaError)
    assert issubclass(MobulaAuthError, MobulaAPIError)
    assert issubclass(MobulaRateLimitError, MobulaAPIError)


def test_api_error_carries_status_code_and_message():
    err = MobulaAPIError("boom", status_code=500)
    assert err.status_code == 500
    assert "boom" in str(err)


def test_rate_limit_error_carries_retry_after():
    err = MobulaRateLimitError("slow down", status_code=429, retry_after=12.5)
    assert err.status_code == 429
    assert err.retry_after == 12.5


def test_mobula_error_is_raisable():
    with pytest.raises(MobulaError):
        raise MobulaError("base failure")
