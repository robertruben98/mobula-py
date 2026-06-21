"""Synchronous quickstart for mobula-py.

Run with a free Mobula API key (https://mobula.io):

    MOBULA_API_KEY=your-key python examples/quickstart.py
"""

import os

from mobula import MobulaClient


def main() -> None:
    api_key = os.environ.get("MOBULA_API_KEY")  # optional, but recommended
    with MobulaClient(api_key=api_key) as client:
        btc = client.get_market_data(asset="Bitcoin")
        print(f"BTC price:      ${btc.price:,.2f}")
        print(f"BTC market cap: ${btc.market_cap:,.0f}")

        many = client.get_multi_market_data(assets=["Bitcoin", "Ethereum"])
        for name, data in many.items():
            print(f"{name}: ${data.price:,.2f}")

        chains = client.get_blockchains()
        print(f"Supported chains: {len(chains)}")


if __name__ == "__main__":
    main()
