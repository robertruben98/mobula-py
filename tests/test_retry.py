"""Tests for HTTP 429 rate-limit handling and retry/backoff."""

import httpx
import pytest
import respx

from mobula import MobulaClient, MobulaRateLimitError
from mobula.models import MarketData

BASE = "https://api.mobula.io/api/1"


@respx.mock
def test_retries_after_429_then_succeeds():
    route = respx.get(f"{BASE}/market/data").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}),
            httpx.Response(200, json={"data": {"price": 1.0}}),
        ]
    )
    # max_retries>=1 and a zero base so the test is fast.
    client = MobulaClient(max_retries=2, backoff_factor=0.0)
    result = client.get_market_data(asset="Bitcoin")
    assert isinstance(result, MarketData)
    assert result.price == 1.0
    assert route.call_count == 2


@respx.mock
def test_raises_rate_limit_error_after_exhausting_retries():
    respx.get(f"{BASE}/market/data").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "0"})
    )
    client = MobulaClient(max_retries=1, backoff_factor=0.0)
    with pytest.raises(MobulaRateLimitError) as exc_info:
        client.get_market_data(asset="Bitcoin")
    assert exc_info.value.status_code == 429


@respx.mock
def test_rate_limit_error_parses_retry_after():
    respx.get(f"{BASE}/market/data").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "5"})
    )
    client = MobulaClient(max_retries=0, backoff_factor=0.0)
    with pytest.raises(MobulaRateLimitError) as exc_info:
        client.get_market_data(asset="Bitcoin")
    assert exc_info.value.retry_after == 5.0


@respx.mock
def test_no_retry_when_max_retries_zero():
    route = respx.get(f"{BASE}/market/data").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "0"})
    )
    client = MobulaClient(max_retries=0, backoff_factor=0.0)
    with pytest.raises(MobulaRateLimitError):
        client.get_market_data(asset="Bitcoin")
    assert route.call_count == 1
