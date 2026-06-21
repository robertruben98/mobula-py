"""mobula-py: a typed Python client for the Mobula API.

Example:
    >>> from mobula import MobulaClient
    >>> client = MobulaClient(api_key="your-api-key")
    >>> data = client.get_market_data(asset="Bitcoin")
    >>> print(data.price)
"""

from mobula.async_client import AsyncMobulaClient
from mobula.client import MobulaClient
from mobula.exceptions import (
    MobulaAPIError,
    MobulaAuthError,
    MobulaError,
    MobulaRateLimitError,
)
from mobula.models import (
    OHLCV,
    Blockchain,
    MarketData,
    Metadata,
    WalletAsset,
    WalletPortfolio,
    WalletTransaction,
)

__version__ = "0.1.0"

__all__ = [
    "OHLCV",
    "AsyncMobulaClient",
    "Blockchain",
    "MarketData",
    "Metadata",
    "MobulaAPIError",
    "MobulaAuthError",
    "MobulaClient",
    "MobulaError",
    "MobulaRateLimitError",
    "WalletAsset",
    "WalletPortfolio",
    "WalletTransaction",
    "__version__",
]
