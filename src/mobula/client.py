"""Synchronous client for the Mobula API."""

import time
from collections.abc import Mapping
from types import TracebackType
from typing import Any, Optional

import httpx

from mobula._base import (
    DEFAULT_BACKOFF_FACTOR,
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    as_model_list,
    backoff_delay,
    build_headers,
    clean_params,
    handle_response,
    is_retryable,
    parse_retry_after,
)
from mobula.models import (
    OHLCV,
    Blockchain,
    MarketData,
    Metadata,
    WalletPortfolio,
    WalletTransaction,
)


class MobulaClient:
    """A synchronous client for the Mobula REST API.

    The client wraps an :class:`httpx.Client`, transparently adds the
    ``Authorization`` header when an ``api_key`` is supplied, unwraps the
    ``data`` envelope returned by every endpoint, and retries on HTTP 429 and
    5xx responses with exponential backoff.

    Args:
        api_key: Mobula API key. When omitted, requests are unauthenticated and
            are subject to the demo/free-tier rate limits (free keys are
            available at https://mobula.io).
        base_url: Override the API base URL (defaults to the production API).
        timeout: Per-request timeout in seconds.
        max_retries: Maximum number of retries for rate-limited / server errors.
        backoff_factor: Base multiplier for exponential backoff, in seconds.
        client: An existing :class:`httpx.Client` to reuse (advanced use).

    Example:
        >>> from mobula import MobulaClient
        >>> with MobulaClient(api_key="your-api-key") as client:
        ...     btc = client.get_market_data(asset="Bitcoin")
        ...     print(btc.price)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self.base_url = base_url
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self._owns_client = client is None
        self._client = client or httpx.Client(
            base_url=base_url,
            headers=build_headers(api_key),
            timeout=timeout,
        )

    def __enter__(self) -> "MobulaClient":
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP client (only if this instance created it)."""
        if self._owns_client:
            self._client.close()

    def _request(self, method: str, path: str, *, params: Mapping[str, Any]) -> Any:
        """Perform a request with retry/backoff and return the unwrapped payload."""
        cleaned = clean_params(params)
        attempt = 0
        while True:
            response = self._client.request(method, path, params=cleaned)
            if is_retryable(response) and attempt < self.max_retries:
                delay = backoff_delay(attempt, self.backoff_factor, parse_retry_after(response))
                if delay > 0:
                    time.sleep(delay)
                attempt += 1
                continue
            return handle_response(response)

    def get_market_data(
        self,
        *,
        asset: Optional[str] = None,
        symbol: Optional[str] = None,
        blockchain: Optional[str] = None,
    ) -> MarketData:
        """Fetch real-time market data for a single asset.

        Provide at least one of ``asset`` (name or contract address), ``symbol``
        (ticker), optionally narrowed by ``blockchain``.

        Args:
            asset: Asset name or on-chain contract address (e.g. ``"Bitcoin"``).
            symbol: Ticker symbol (e.g. ``"BTC"``).
            blockchain: Chain identifier to disambiguate on-chain assets.

        Returns:
            The parsed :class:`~mobula.models.MarketData`.
        """
        payload = self._request(
            "GET",
            "/market/data",
            params={"asset": asset, "symbol": symbol, "blockchain": blockchain},
        )
        return MarketData.model_validate(payload)

    def get_multi_market_data(
        self,
        *,
        assets: list[str],
        blockchains: Optional[list[str]] = None,
    ) -> dict[str, MarketData]:
        """Fetch market data for many assets in a single request.

        Args:
            assets: Asset names, symbols, or contract addresses.
            blockchains: Optional per-asset chains, matched by order.

        Returns:
            A mapping of asset key to its :class:`~mobula.models.MarketData`.
        """
        payload = self._request(
            "GET",
            "/market/multi-data",
            params={
                "assets": ",".join(assets),
                "blockchains": ",".join(blockchains) if blockchains else None,
            },
        )
        if isinstance(payload, dict):
            return {key: MarketData.model_validate(value) for key, value in payload.items()}
        return {}

    def get_metadata(
        self,
        *,
        asset: Optional[str] = None,
        symbol: Optional[str] = None,
        blockchain: Optional[str] = None,
    ) -> Metadata:
        """Fetch descriptive metadata (logo, description, socials) for an asset.

        Args:
            asset: Asset name or on-chain contract address.
            symbol: Ticker symbol.
            blockchain: Chain identifier to disambiguate on-chain assets.

        Returns:
            The parsed :class:`~mobula.models.Metadata`.
        """
        payload = self._request(
            "GET",
            "/metadata",
            params={"asset": asset, "symbol": symbol, "blockchain": blockchain},
        )
        return Metadata.model_validate(payload)

    def get_market_history(
        self,
        *,
        asset: Optional[str] = None,
        symbol: Optional[str] = None,
        blockchain: Optional[str] = None,
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
    ) -> list[OHLCV]:
        """Fetch historical price/OHLCV candles for an asset.

        Args:
            asset: Asset name or on-chain contract address.
            symbol: Ticker symbol.
            blockchain: Chain identifier to disambiguate on-chain assets.
            from_timestamp: Start of the window, in milliseconds since epoch.
            to_timestamp: End of the window, in milliseconds since epoch.

        Returns:
            A list of :class:`~mobula.models.OHLCV` candles.
        """
        payload = self._request(
            "GET",
            "/market/history",
            params={
                "asset": asset,
                "symbol": symbol,
                "blockchain": blockchain,
                "from": from_timestamp,
                "to": to_timestamp,
            },
        )
        return _parse_history(payload)

    def get_blockchains(self) -> list[Blockchain]:
        """List the blockchains supported by Mobula.

        Returns:
            A list of :class:`~mobula.models.Blockchain`.
        """
        payload = self._request("GET", "/market/blockchains", params={})
        return as_model_list(payload, Blockchain)

    def get_wallet_portfolio(
        self,
        *,
        wallet: str,
        blockchains: Optional[list[str]] = None,
    ) -> WalletPortfolio:
        """Fetch the aggregated portfolio for a wallet address.

        Args:
            wallet: The wallet address to inspect.
            blockchains: Optional list of chains to restrict the query to.

        Returns:
            The parsed :class:`~mobula.models.WalletPortfolio`.
        """
        payload = self._request(
            "GET",
            "/wallet/portfolio",
            params={
                "wallet": wallet,
                "blockchains": ",".join(blockchains) if blockchains else None,
            },
        )
        return WalletPortfolio.model_validate(payload)

    def get_wallet_transactions(
        self,
        *,
        wallet: str,
        blockchains: Optional[list[str]] = None,
    ) -> list[WalletTransaction]:
        """Fetch on-chain transactions for a wallet address.

        Args:
            wallet: The wallet address to inspect.
            blockchains: Optional list of chains to restrict the query to.

        Returns:
            A list of :class:`~mobula.models.WalletTransaction`.
        """
        payload = self._request(
            "GET",
            "/wallet/transactions",
            params={
                "wallet": wallet,
                "blockchains": ",".join(blockchains) if blockchains else None,
            },
        )
        return as_model_list(payload, WalletTransaction)


def _parse_history(payload: Any) -> list[OHLCV]:
    """Parse a ``/market/history`` payload into OHLCV candles.

    The endpoint returns candles either under a ``price_history`` key as
    positional ``[time, o, h, l, c, v]`` rows, or directly as a list.
    """
    rows: Any = payload
    if isinstance(payload, dict):
        rows = payload.get("price_history", [])
    if not isinstance(rows, list):
        return []
    candles: list[OHLCV] = []
    for row in rows:
        if isinstance(row, list):
            candles.append(OHLCV.from_row(row))
        elif isinstance(row, dict):
            candles.append(OHLCV.model_validate(row))
    return candles
