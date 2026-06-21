"""Pydantic models for Mobula API responses.

All models use ``extra="allow"`` so that fields added by the Mobula API in the
future are preserved on the parsed object rather than discarded. Most fields are
declared ``Optional`` because the API omits values that are not available for a
given asset, chain or wallet.
"""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class MobulaModel(BaseModel):
    """Base model that retains unknown fields returned by the API."""

    model_config = ConfigDict(extra="allow")


class MarketData(MobulaModel):
    """Real-time market data for a single asset.

    Returned by ``GET /market/data`` and as the per-asset value of
    ``GET /market/multi-data``.
    """

    price: Optional[float] = Field(default=None, description="Current price in USD.")
    market_cap: Optional[float] = Field(default=None, description="Market capitalisation in USD.")
    market_cap_diluted: Optional[float] = Field(
        default=None, description="Fully diluted market capitalisation in USD."
    )
    volume: Optional[float] = Field(default=None, description="24h trading volume in USD.")
    liquidity: Optional[float] = Field(default=None, description="Available liquidity in USD.")
    price_change_24h: Optional[float] = Field(
        default=None, description="Price change over the last 24 hours, in percent."
    )
    name: Optional[str] = Field(default=None, description="Human-readable asset name.")
    symbol: Optional[str] = Field(default=None, description="Ticker symbol of the asset.")
    decimals: Optional[int] = Field(
        default=None, description="Token decimals, for on-chain assets."
    )
    total_supply: Optional[float] = Field(default=None, description="Total token supply.")
    circulating_supply: Optional[float] = Field(
        default=None, description="Circulating token supply."
    )


class Metadata(MobulaModel):
    """Descriptive metadata for an asset, returned by ``GET /metadata``."""

    id: Optional[int] = Field(default=None, description="Mobula internal asset id.")
    name: Optional[str] = Field(default=None, description="Human-readable asset name.")
    symbol: Optional[str] = Field(default=None, description="Ticker symbol of the asset.")
    description: Optional[str] = Field(default=None, description="Long-form asset description.")
    logo: Optional[str] = Field(default=None, description="URL of the asset logo.")
    website: Optional[str] = Field(default=None, description="Official website URL.")
    twitter: Optional[str] = Field(default=None, description="Twitter/X profile URL or handle.")


class OHLCV(MobulaModel):
    """A single open/high/low/close/volume candle from price history."""

    time: Optional[int] = Field(default=None, description="Candle timestamp in milliseconds.")
    open: Optional[float] = Field(default=None, description="Opening price.")
    high: Optional[float] = Field(default=None, description="Highest price in the period.")
    low: Optional[float] = Field(default=None, description="Lowest price in the period.")
    close: Optional[float] = Field(default=None, description="Closing price.")
    volume: Optional[float] = Field(default=None, description="Volume traded in the period.")

    @classmethod
    def from_row(cls, row: list[Any]) -> "OHLCV":
        """Build an :class:`OHLCV` from a positional ``[time, o, h, l, c, v]`` row.

        Mobula's ``GET /market/history`` returns candles as positional arrays
        rather than objects; this helper maps them onto named fields.

        Args:
            row: A sequence of ``[time, open, high, low, close, volume]``. Trailing
                items may be omitted.

        Returns:
            The parsed candle.
        """
        keys = ("time", "open", "high", "low", "close", "volume")
        return cls(**{key: row[index] for index, key in enumerate(keys) if index < len(row)})


class Blockchain(MobulaModel):
    """A blockchain supported by Mobula, from ``GET /market/blockchains``."""

    name: Optional[str] = Field(default=None, description="Display name of the blockchain.")
    chainId: Optional[str] = Field(default=None, description="Numeric chain id as a string.")
    evmChainId: Optional[int] = Field(default=None, description="EVM chain id, when applicable.")


class WalletAsset(MobulaModel):
    """A single holding within a wallet portfolio."""

    asset: Optional[Any] = Field(default=None, description="Asset descriptor for this holding.")
    token_balance: Optional[float] = Field(default=None, description="Token balance held.")
    estimated_balance: Optional[float] = Field(
        default=None, description="Estimated USD value of the holding."
    )
    price: Optional[float] = Field(default=None, description="Current unit price in USD.")


class WalletPortfolio(MobulaModel):
    """Aggregated portfolio for one or more wallets.

    Returned by ``GET /wallet/portfolio``.
    """

    total_wallet_balance: Optional[float] = Field(
        default=None, description="Total estimated portfolio value in USD."
    )
    wallets: Optional[list[str]] = Field(
        default=None, description="Wallet addresses included in the portfolio."
    )
    assets: Optional[list[WalletAsset]] = Field(
        default=None, description="Individual holdings making up the portfolio."
    )


class WalletTransaction(MobulaModel):
    """A single on-chain transaction from ``GET /wallet/transactions``."""

    hash: Optional[str] = Field(default=None, description="Transaction hash.")
    timestamp: Optional[int] = Field(default=None, description="Transaction timestamp (ms).")
    blockchain: Optional[str] = Field(
        default=None, description="Chain the transaction occurred on."
    )
    amount: Optional[float] = Field(default=None, description="Token amount transacted.")
    amount_usd: Optional[float] = Field(default=None, description="USD value at transaction time.")
    type: Optional[str] = Field(
        default=None, description="Transaction type, e.g. buy/sell/transfer."
    )
    from_address: Optional[str] = Field(default=None, alias="from", description="Sender address.")
    to_address: Optional[str] = Field(default=None, alias="to", description="Recipient address.")
