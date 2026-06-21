"""Live integration test against the real Mobula API.

Marked ``integration`` so it is deselected by default (see ``addopts`` in
``pyproject.toml``). Run explicitly with a real key:

    MOBULA_API_KEY=... pytest -m integration

It is skipped automatically when ``MOBULA_API_KEY`` is not set.
"""

import os

import pytest

from mobula import MobulaClient
from mobula.models import MarketData

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    not os.environ.get("MOBULA_API_KEY"),
    reason="MOBULA_API_KEY not set; skipping live integration test.",
)
def test_live_get_market_data_for_bitcoin():
    with MobulaClient(api_key=os.environ["MOBULA_API_KEY"]) as client:
        data = client.get_market_data(asset="Bitcoin")
    assert isinstance(data, MarketData)
    assert data.price is not None and data.price > 0
