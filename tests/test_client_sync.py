"""Unit tests for the synchronous MobulaClient (respx-mocked, no network)."""

import httpx
import pytest
import respx

from mobula import MobulaClient
from mobula.models import OHLCV, Blockchain, MarketData, Metadata, WalletPortfolio

BASE = "https://api.mobula.io/api/1"


def test_default_base_url_and_no_auth_header_without_key():
    client = MobulaClient()
    assert str(client.base_url).rstrip("/") == BASE
    assert "Authorization" not in client._client.headers


def test_api_key_sets_authorization_header_raw():
    # Mobula expects the raw key in Authorization, with NO "Bearer " prefix.
    client = MobulaClient(api_key="secret-key")
    assert client._client.headers["Authorization"] == "secret-key"


def test_base_url_is_configurable():
    client = MobulaClient(base_url="https://demo-api.mobula.io/api/1")
    assert str(client.base_url).rstrip("/") == "https://demo-api.mobula.io/api/1"


@respx.mock
def test_get_market_data_unwraps_data_and_sends_params():
    route = respx.get(f"{BASE}/market/data").mock(
        return_value=httpx.Response(200, json={"data": {"price": 65000.0, "symbol": "BTC"}})
    )
    client = MobulaClient(api_key="k")
    result = client.get_market_data(asset="Bitcoin")
    assert isinstance(result, MarketData)
    assert result.price == 65000.0
    assert route.calls.last.request.url.params["asset"] == "Bitcoin"
    assert route.calls.last.request.headers["Authorization"] == "k"


@respx.mock
def test_get_multi_market_data_returns_mapping():
    respx.get(f"{BASE}/market/multi-data").mock(
        return_value=httpx.Response(
            200,
            json={"data": {"Bitcoin": {"price": 1.0}, "Ethereum": {"price": 2.0}}},
        )
    )
    client = MobulaClient()
    result = client.get_multi_market_data(assets=["Bitcoin", "Ethereum"])
    assert set(result.keys()) == {"Bitcoin", "Ethereum"}
    assert isinstance(result["Bitcoin"], MarketData)
    assert result["Ethereum"].price == 2.0


@respx.mock
def test_get_metadata():
    respx.get(f"{BASE}/metadata").mock(
        return_value=httpx.Response(200, json={"data": {"name": "Ethereum", "symbol": "ETH"}})
    )
    client = MobulaClient()
    meta = client.get_metadata(asset="Ethereum")
    assert isinstance(meta, Metadata)
    assert meta.symbol == "ETH"


@respx.mock
def test_get_market_history_returns_ohlcv_list():
    respx.get(f"{BASE}/market/history").mock(
        return_value=httpx.Response(
            200,
            json={"data": {"price_history": [[1700000000000, 1.0, 2.0, 0.5, 1.5, 100.0]]}},
        )
    )
    client = MobulaClient()
    history = client.get_market_history(asset="Bitcoin")
    assert len(history) == 1
    assert isinstance(history[0], OHLCV)
    assert history[0].close == 1.5


@respx.mock
def test_get_blockchains_returns_list():
    respx.get(f"{BASE}/market/blockchains").mock(
        return_value=httpx.Response(200, json={"data": [{"name": "Ethereum", "chainId": "1"}]})
    )
    client = MobulaClient()
    chains = client.get_blockchains()
    assert isinstance(chains[0], Blockchain)
    assert chains[0].name == "Ethereum"


@respx.mock
def test_get_wallet_portfolio():
    respx.get(f"{BASE}/wallet/portfolio").mock(
        return_value=httpx.Response(
            200, json={"data": {"total_wallet_balance": 100.0, "assets": []}}
        )
    )
    client = MobulaClient()
    portfolio = client.get_wallet_portfolio(wallet="0xabc")
    assert isinstance(portfolio, WalletPortfolio)
    assert portfolio.total_wallet_balance == 100.0


@respx.mock
def test_get_wallet_transactions_returns_list():
    respx.get(f"{BASE}/wallet/transactions").mock(
        return_value=httpx.Response(200, json={"data": [{"hash": "0xdead", "amount": 5.0}]})
    )
    client = MobulaClient()
    txs = client.get_wallet_transactions(wallet="0xabc")
    assert len(txs) == 1
    assert txs[0].hash == "0xdead"


def test_client_works_as_context_manager():
    with MobulaClient() as client:
        assert isinstance(client, MobulaClient)


@respx.mock
def test_raises_auth_error_on_401():
    from mobula import MobulaAuthError

    respx.get(f"{BASE}/market/data").mock(return_value=httpx.Response(401, json={"error": "nope"}))
    client = MobulaClient()
    with pytest.raises(MobulaAuthError):
        client.get_market_data(asset="Bitcoin")


@respx.mock
def test_raises_api_error_on_500():
    from mobula import MobulaAPIError

    respx.get(f"{BASE}/market/data").mock(return_value=httpx.Response(500, text="boom"))
    client = MobulaClient()
    with pytest.raises(MobulaAPIError) as exc_info:
        client.get_market_data(asset="Bitcoin")
    assert exc_info.value.status_code == 500
