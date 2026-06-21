"""Asynchronous quickstart for mobula-py.

Run with a free Mobula API key (https://mobula.io):

    MOBULA_API_KEY=your-key python examples/async_quickstart.py
"""

import asyncio
import os

from mobula import AsyncMobulaClient


async def main() -> None:
    api_key = os.environ.get("MOBULA_API_KEY")  # optional, but recommended
    async with AsyncMobulaClient(api_key=api_key) as client:
        # Fetch several assets concurrently.
        btc, eth = await asyncio.gather(
            client.get_market_data(asset="Bitcoin"),
            client.get_market_data(asset="Ethereum"),
        )
        print(f"BTC: ${btc.price:,.2f}")
        print(f"ETH: ${eth.price:,.2f}")

        history = await client.get_market_history(asset="Bitcoin")
        print(f"History points: {len(history)}")


if __name__ == "__main__":
    asyncio.run(main())
