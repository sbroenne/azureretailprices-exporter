"""Opt-in one-page Azure smoke tests."""

import os

import pytest

from api import azureapi

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.getenv("RUN_LIVE_AZURE_TESTS") != "1",
        reason="Set RUN_LIVE_AZURE_TESTS=1 to run live Azure smoke tests",
    ),
]


def test_live_get_price_data_smoke() -> None:
    records = azureapi.get_price_data("USD", max_pages=1)
    assert records
    assert "retailPrice" in records[0]


def test_live_calculate_fx_rates_smoke() -> None:
    rates = azureapi.calculate_fx_rates(
        target_currencies=["EUR"],
        results_filter="$filter=meterId eq '5daea80f-04ac-5385-86f0-b263d23becd2'",
        max_pages=1,
    )
    assert rates["currency"].tolist() == ["EUR"]
    assert rates["fxRate"].iloc[0] > 0
