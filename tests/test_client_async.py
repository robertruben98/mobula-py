"""Unit tests for the asynchronous AsyncMobulaClient (respx-mocked, no network)."""

import httpx
import pytest
import respx

from mobula import AsyncMobulaClient, MobulaAuthError, MobulaRateLimitError
from mobula.models import OHLCV, Blockchain, MarketData, Metadata, WalletPortfolio

BASE = "https://api.mobula.io/api/1"


def test_async_api_key_sets_authorization_header_raw():
    client = AsyncMobulaClient(api_key="secret-key")
    assert client._client.headers["Authorization"] == "secret-key"


@respx.mock
async def test_async_get_market_data():
    route = respx.get(f"{BASE}/market/data").mock(
        return_value=httpx.Response(200, json={"data": {"price": 65000.0, "symbol": "BTC"}})
    )
    async with AsyncMobulaClient(api_key="k") as client:
        result = await client.get_market_data(asset="Bitcoin")
    assert isinstance(result, MarketData)
    assert result.price == 65000.0
    assert route.calls.last.request.headers["Authorization"] == "k"


@respx.mock
async def test_async_get_multi_market_data():
    respx.get(f"{BASE}/market/multi-data").mock(
        return_value=httpx.Response(
            200, json={"data": {"Bitcoin": {"price": 1.0}, "Ethereum": {"price": 2.0}}}
        )
    )
    async with AsyncMobulaClient() as client:
        result = await client.get_multi_market_data(assets=["Bitcoin", "Ethereum"])
    assert result["Ethereum"].price == 2.0


@respx.mock
async def test_async_get_metadata():
    respx.get(f"{BASE}/metadata").mock(
        return_value=httpx.Response(200, json={"data": {"name": "Ethereum", "symbol": "ETH"}})
    )
    async with AsyncMobulaClient() as client:
        meta = await client.get_metadata(asset="Ethereum")
    assert isinstance(meta, Metadata)
    assert meta.symbol == "ETH"


@respx.mock
async def test_async_get_market_history():
    respx.get(f"{BASE}/market/history").mock(
        return_value=httpx.Response(
            200, json={"data": {"price_history": [[1700000000000, 1.0, 2.0, 0.5, 1.5, 100.0]]}}
        )
    )
    async with AsyncMobulaClient() as client:
        history = await client.get_market_history(asset="Bitcoin")
    assert isinstance(history[0], OHLCV)
    assert history[0].close == 1.5


@respx.mock
async def test_async_get_blockchains():
    respx.get(f"{BASE}/market/blockchains").mock(
        return_value=httpx.Response(200, json={"data": [{"name": "Ethereum"}]})
    )
    async with AsyncMobulaClient() as client:
        chains = await client.get_blockchains()
    assert isinstance(chains[0], Blockchain)


@respx.mock
async def test_async_get_wallet_portfolio():
    respx.get(f"{BASE}/wallet/portfolio").mock(
        return_value=httpx.Response(200, json={"data": {"total_wallet_balance": 100.0}})
    )
    async with AsyncMobulaClient() as client:
        portfolio = await client.get_wallet_portfolio(wallet="0xabc")
    assert isinstance(portfolio, WalletPortfolio)
    assert portfolio.total_wallet_balance == 100.0


@respx.mock
async def test_async_get_wallet_transactions():
    respx.get(f"{BASE}/wallet/transactions").mock(
        return_value=httpx.Response(200, json={"data": [{"hash": "0xdead"}]})
    )
    async with AsyncMobulaClient() as client:
        txs = await client.get_wallet_transactions(wallet="0xabc")
    assert txs[0].hash == "0xdead"


@respx.mock
async def test_async_retries_after_429():
    route = respx.get(f"{BASE}/market/data").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}),
            httpx.Response(200, json={"data": {"price": 1.0}}),
        ]
    )
    async with AsyncMobulaClient(max_retries=2, backoff_factor=0.0) as client:
        result = await client.get_market_data(asset="Bitcoin")
    assert result.price == 1.0
    assert route.call_count == 2


@respx.mock
async def test_async_raises_rate_limit_after_exhaustion():
    respx.get(f"{BASE}/market/data").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "0"})
    )
    async with AsyncMobulaClient(max_retries=0, backoff_factor=0.0) as client:
        with pytest.raises(MobulaRateLimitError):
            await client.get_market_data(asset="Bitcoin")


@respx.mock
async def test_async_raises_auth_error_on_401():
    respx.get(f"{BASE}/market/data").mock(return_value=httpx.Response(401))
    async with AsyncMobulaClient() as client:
        with pytest.raises(MobulaAuthError):
            await client.get_market_data(asset="Bitcoin")
