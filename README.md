# mobula-py

[![CI](https://github.com/robertruben98/mobula-py/actions/workflows/ci.yml/badge.svg)](https://github.com/robertruben98/mobula-py/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/mobula-py.svg)](https://pypi.org/project/mobula-py/)
[![Docs](https://img.shields.io/badge/docs-online-blue)](https://robertruben98.github.io/mobula-py/)
[![Python versions](https://img.shields.io/pypi/pyversions/mobula-py.svg)](https://pypi.org/project/mobula-py/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/robertruben98/mobula-py/blob/main/LICENSE)
[![Typed](https://img.shields.io/badge/types-mypy%20strict-blue.svg)](https://mypy-lang.org/)

A typed, modern Python client for the [Mobula API](https://docs.mobula.io) —
multi-chain crypto market data, asset metadata, price history, and on-chain
wallet data.

- **Sync and async** clients backed by [httpx](https://www.python-httpx.org/).
- **Typed models** powered by [pydantic v2](https://docs.pydantic.dev/) (and
  forward-compatible — unknown API fields are preserved).
- **Resilient**: automatic retry with exponential backoff on HTTP 429 / 5xx,
  honouring the `Retry-After` header.
- **`py.typed`**: ships type information; passes `mypy --strict`.
- Python **3.9+**.

## Installation

```bash
pip install mobula-py
```

> The package is named `mobula-py` on PyPI but imported as `mobula`.

## API key

Most endpoints require a Mobula API key. A **free** key is available at
[mobula.io](https://mobula.io). Without a key, requests use the demo/free tier
and are rate limited (you will see `429` responses quickly). The key is sent in
the `Authorization` header.

```python
from mobula import MobulaClient

client = MobulaClient(api_key="your-api-key")  # or read from an env var
```

## Quickstart

```python
from mobula import MobulaClient

with MobulaClient(api_key="your-api-key") as client:
    btc = client.get_market_data(asset="Bitcoin")
    print(btc.price, btc.market_cap)

    many = client.get_multi_market_data(assets=["Bitcoin", "Ethereum"])
    print(many["Ethereum"].price)

    meta = client.get_metadata(symbol="ETH")
    print(meta.website)

    history = client.get_market_history(asset="Bitcoin")
    print(history[0].close)

    chains = client.get_blockchains()
    print([c.name for c in chains[:3]])

    portfolio = client.get_wallet_portfolio(wallet="0x...")
    print(portfolio.total_wallet_balance)
```

### Async

```python
import asyncio
from mobula import AsyncMobulaClient

async def main():
    async with AsyncMobulaClient(api_key="your-api-key") as client:
        btc = await client.get_market_data(asset="Bitcoin")
        print(btc.price)

asyncio.run(main())
```

## Configuration

```python
MobulaClient(
    api_key="your-api-key",
    base_url="https://api.mobula.io/api/1",  # configurable (e.g. demo-api.mobula.io)
    timeout=30.0,
    max_retries=2,        # retries on 429 / 5xx
    backoff_factor=0.5,   # exponential backoff base, in seconds
)
```

## Error handling

```python
from mobula import (
    MobulaClient,
    MobulaError,          # base class for everything below
    MobulaAPIError,       # non-2xx response (carries .status_code)
    MobulaAuthError,      # 401 / 403 — bad or missing api_key
    MobulaRateLimitError, # 429 — carries .retry_after
)

client = MobulaClient(api_key="your-api-key")
try:
    data = client.get_market_data(asset="Bitcoin")
except MobulaRateLimitError as exc:
    print(f"Rate limited, retry after {exc.retry_after}s")
except MobulaAPIError as exc:
    print(f"API error {exc.status_code}")
```

## Endpoints

| Method | Endpoint | Returns |
| --- | --- | --- |
| `get_market_data` | `GET /market/data` | `MarketData` |
| `get_multi_market_data` | `GET /market/multi-data` | `dict[str, MarketData]` |
| `get_metadata` | `GET /metadata` | `Metadata` |
| `get_market_history` | `GET /market/history` | `list[OHLCV]` |
| `get_blockchains` | `GET /market/blockchains` | `list[Blockchain]` |
| `get_wallet_portfolio` | `GET /wallet/portfolio` | `WalletPortfolio` |
| `get_wallet_transactions` | `GET /wallet/transactions` | `list[WalletTransaction]` |

See the [`examples/`](examples/) directory for runnable scripts.

## Development

```bash
pip install -e ".[dev]"
ruff check src tests
ruff format --check src tests
mypy --strict src
pytest                 # unit tests (network-mocked)
pytest -m integration  # live tests — requires MOBULA_API_KEY
```

## License

MIT — see [LICENSE](LICENSE).
