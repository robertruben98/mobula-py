"""Tests for the pydantic data models."""

from mobula.models import (
    OHLCV,
    Blockchain,
    MarketData,
    Metadata,
    WalletPortfolio,
)


def test_market_data_parses_core_fields():
    md = MarketData.model_validate(
        {
            "price": 65000.5,
            "market_cap": 1_200_000_000_000,
            "volume": 25_000_000_000,
            "liquidity": 500_000_000,
            "name": "Bitcoin",
            "symbol": "BTC",
            "price_change_24h": 1.5,
        }
    )
    assert md.price == 65000.5
    assert md.symbol == "BTC"
    assert md.price_change_24h == 1.5


def test_market_data_allows_unknown_fields():
    md = MarketData.model_validate({"price": 1.0, "some_future_field": "kept"})
    # extra="allow" means the unknown field is retained on the model.
    assert md.some_future_field == "kept"  # type: ignore[attr-defined]


def test_market_data_tolerates_missing_optional_fields():
    md = MarketData.model_validate({"price": 42.0})
    assert md.price == 42.0
    assert md.symbol is None


def test_metadata_parses():
    meta = Metadata.model_validate(
        {"name": "Ethereum", "symbol": "ETH", "website": "https://ethereum.org"}
    )
    assert meta.name == "Ethereum"
    assert meta.website == "https://ethereum.org"


def test_ohlcv_parses_list_row_form():
    # Mobula history rows arrive as [timestamp_ms, open, high, low, close, volume].
    row = OHLCV.from_row([1700000000000, 1.0, 2.0, 0.5, 1.5, 100.0])
    assert row.time == 1700000000000
    assert row.open == 1.0
    assert row.high == 2.0
    assert row.low == 0.5
    assert row.close == 1.5
    assert row.volume == 100.0


def test_blockchain_parses():
    chain = Blockchain.model_validate({"name": "Ethereum", "chainId": "1"})
    assert chain.name == "Ethereum"


def test_wallet_portfolio_parses():
    portfolio = WalletPortfolio.model_validate(
        {"total_wallet_balance": 1234.56, "wallets": ["0xabc"], "assets": []}
    )
    assert portfolio.total_wallet_balance == 1234.56
    assert portfolio.wallets == ["0xabc"]
