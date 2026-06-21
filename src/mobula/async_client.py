"""Asynchronous client for the Mobula API."""

import asyncio
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
from mobula.client import _parse_history
from mobula.models import (
    OHLCV,
    Blockchain,
    MarketData,
    Metadata,
    WalletPortfolio,
    WalletTransaction,
)


class AsyncMobulaClient:
    """An asyncio client for the Mobula REST API.

    This is the ``async``/``await`` counterpart of :class:`~mobula.MobulaClient`
    and exposes the same methods and behaviour (auth header, ``data`` unwrapping,
    retry on 429/5xx) backed by an :class:`httpx.AsyncClient`.

    Args:
        api_key: Mobula API key. When omitted, requests are unauthenticated and
            subject to the demo/free-tier rate limits.
        base_url: Override the API base URL (defaults to the production API).
        timeout: Per-request timeout in seconds.
        max_retries: Maximum number of retries for rate-limited / server errors.
        backoff_factor: Base multiplier for exponential backoff, in seconds.
        client: An existing :class:`httpx.AsyncClient` to reuse (advanced use).

    Example:
        >>> import asyncio
        >>> from mobula import AsyncMobulaClient
        >>> async def main():
        ...     async with AsyncMobulaClient(api_key="your-api-key") as client:
        ...         btc = await client.get_market_data(asset="Bitcoin")
        ...         print(btc.price)
        >>> asyncio.run(main())
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self.base_url = base_url
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=base_url,
            headers=build_headers(api_key),
            timeout=timeout,
        )

    async def __aenter__(self) -> "AsyncMobulaClient":
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP client (only if this instance created it)."""
        if self._owns_client:
            await self._client.aclose()

    async def _request(self, method: str, path: str, *, params: Mapping[str, Any]) -> Any:
        """Perform a request with retry/backoff and return the unwrapped payload."""
        cleaned = clean_params(params)
        attempt = 0
        while True:
            response = await self._client.request(method, path, params=cleaned)
            if is_retryable(response) and attempt < self.max_retries:
                delay = backoff_delay(attempt, self.backoff_factor, parse_retry_after(response))
                if delay > 0:
                    await asyncio.sleep(delay)
                attempt += 1
                continue
            return handle_response(response)

    async def get_market_data(
        self,
        *,
        asset: Optional[str] = None,
        symbol: Optional[str] = None,
        blockchain: Optional[str] = None,
    ) -> MarketData:
        """Fetch real-time market data for a single asset.

        Args:
            asset: Asset name or on-chain contract address (e.g. ``"Bitcoin"``).
            symbol: Ticker symbol (e.g. ``"BTC"``).
            blockchain: Chain identifier to disambiguate on-chain assets.

        Returns:
            The parsed :class:`~mobula.models.MarketData`.
        """
        payload = await self._request(
            "GET",
            "/market/data",
            params={"asset": asset, "symbol": symbol, "blockchain": blockchain},
        )
        return MarketData.model_validate(payload)

    async def get_multi_market_data(
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
        payload = await self._request(
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

    async def get_metadata(
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
        payload = await self._request(
            "GET",
            "/metadata",
            params={"asset": asset, "symbol": symbol, "blockchain": blockchain},
        )
        return Metadata.model_validate(payload)

    async def get_market_history(
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
        payload = await self._request(
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

    async def get_blockchains(self) -> list[Blockchain]:
        """List the blockchains supported by Mobula.

        Returns:
            A list of :class:`~mobula.models.Blockchain`.
        """
        payload = await self._request("GET", "/market/blockchains", params={})
        return as_model_list(payload, Blockchain)

    async def get_wallet_portfolio(
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
        payload = await self._request(
            "GET",
            "/wallet/portfolio",
            params={
                "wallet": wallet,
                "blockchains": ",".join(blockchains) if blockchains else None,
            },
        )
        return WalletPortfolio.model_validate(payload)

    async def get_wallet_transactions(
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
        payload = await self._request(
            "GET",
            "/wallet/transactions",
            params={
                "wallet": wallet,
                "blockchains": ",".join(blockchains) if blockchains else None,
            },
        )
        return as_model_list(payload, WalletTransaction)
