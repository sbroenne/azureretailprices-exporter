"""Unit tests for azureapi.py."""

import os
from unittest.mock import Mock

import pandas as pd
import pytest

from api import azureapi

RUN_LIVE_AZURE_TESTS = os.getenv("RUN_LIVE_AZURE_TESTS") == "1"


@pytest.fixture
def mocked_session(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Return a mocked cached session and disable the real progress counter."""
    session = Mock()
    monkeypatch.setattr(
        azureapi.requests_cache, "CachedSession", Mock(return_value=session)
    )

    counter = Mock()
    counter.update = Mock()
    monkeypatch.setattr(azureapi.enlighten, "Counter", Mock(return_value=counter))
    return session


def make_response(payload: dict) -> Mock:
    """Create a mocked HTTP response with a JSON payload."""
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = payload
    return response


def test_get_price_data_builds_initial_request_with_params(
    mocked_session: Mock,
) -> None:
    """The first Azure API call should use structured params instead of a raw URL."""
    mocked_session.get.return_value = make_response({"Items": [], "NextPageLink": None})

    azureapi.get_price_data(
        currency_code="USD",
        results_filter="$filter=serviceName eq 'Virtual Machines'",
        max_pages=1,
    )

    assert mocked_session.get.call_count == 1
    args, kwargs = mocked_session.get.call_args
    assert args[0] == "https://prices.azure.com/api/retail/prices"
    assert kwargs["params"] == {
        "api-version": azureapi.API_VERSION,
        "currencyCode": "'USD'",
        "$filter": "serviceName eq 'Virtual Machines'",
    }
    assert kwargs["timeout"] == azureapi.REQUEST_TIMEOUT


def test_get_price_data_follows_next_page_link(mocked_session: Mock) -> None:
    """Pagination should accumulate items and pass the server-provided next link through."""
    mocked_session.get.side_effect = [
        make_response(
            {
                "Items": [{"skuId": "page-1"}],
                "NextPageLink": "https://prices.azure.com/api/retail/prices?$skip=1000",
            }
        ),
        make_response({"Items": [{"skuId": "page-2"}], "NextPageLink": None}),
    ]

    result = azureapi.get_price_data(currency_code="USD", max_pages=2)

    assert result == [{"skuId": "page-1"}, {"skuId": "page-2"}]
    first_call_args, first_call_kwargs = mocked_session.get.call_args_list[0]
    second_call_args, second_call_kwargs = mocked_session.get.call_args_list[1]
    assert first_call_args[0] == "https://prices.azure.com/api/retail/prices"
    assert (
        second_call_args[0] == "https://prices.azure.com/api/retail/prices?$skip=1000"
    )
    assert first_call_kwargs["params"]["currencyCode"] == "'USD'"
    assert second_call_kwargs["params"] is None


def test_get_price_data_raises_for_missing_items(mocked_session: Mock) -> None:
    """Unexpected response payloads should raise a descriptive error."""
    mocked_session.get.return_value = make_response(
        {"Error": {"Code": "InternalServerError", "Message": "Exchange rate not found"}}
    )

    with pytest.raises(ValueError, match="Items"):
        azureapi.get_price_data(currency_code="USD", max_pages=1)


def test_get_prices_expands_savings_plan(monkeypatch: pytest.MonkeyPatch) -> None:
    """Savings plan entries should expand into normal price rows."""
    input_records = [
        {
            "armSkuName": "SKU1",
            "armRegionName": "eastus",
            "meterId": "meter1",
            "type": "Consumption",
            "unitPrice": 10.0,
            "retailPrice": 10.0,
            "savingsPlan": [
                {"term": "1 Year", "unitPrice": 8.0, "retailPrice": 8.0},
                {"term": "3 Years", "unitPrice": 6.0, "retailPrice": 6.0},
            ],
        },
        {
            "armSkuName": "SKU2",
            "armRegionName": "westus",
            "meterId": "meter2",
            "type": "Consumption",
            "unitPrice": 20.0,
            "retailPrice": 20.0,
        },
    ]
    monkeypatch.setattr(azureapi, "get_price_data", Mock(return_value=input_records))

    result = azureapi.get_prices(currency_code="USD", max_pages=1)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    savings_plan_rows = result[result["type"] == "SavingsPlans"]
    assert list(savings_plan_rows["reservationTerm"]) == ["1 Year", "3 Years"]
    assert savings_plan_rows["unitPrice"].tolist() == [8.0, 6.0]
    assert "savingsPlan" not in savings_plan_rows.columns


def test_calculate_fx_rates_returns_expected_rate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FX rates should be calculated from matching base and target products."""
    usd_data = pd.DataFrame(
        {
            "armSkuName": ["SKU1"],
            "armRegionName": ["eastus"],
            "meterId": ["meter1"],
            "retailPrice": [10.0],
        }
    )
    eur_data = pd.DataFrame(
        {
            "armSkuName": ["SKU1"],
            "armRegionName": ["eastus"],
            "meterId": ["meter1"],
            "retailPrice": [8.5],
        }
    )

    def mock_get_prices(
        currency_code: str, results_filter: str = "", max_pages: int = 9999999
    ) -> pd.DataFrame:
        assert max_pages == 1
        if currency_code == "USD":
            return usd_data.copy()
        if currency_code == "EUR":
            return eur_data.copy()
        raise AssertionError(f"Unexpected currency_code {currency_code}")

    monkeypatch.setattr(azureapi, "get_prices", mock_get_prices)

    fx_df = azureapi.calculate_fx_rates(
        base_currency="USD",
        target_currencies=["EUR"],
        max_pages=1,
    )

    assert isinstance(fx_df, pd.DataFrame)
    assert list(fx_df.columns) == ["currency", "fxRate"]
    assert fx_df.to_dict("records") == [{"currency": "EUR", "fxRate": 0.85}]


def test_calculate_fx_rates_raises_when_target_currency_has_no_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing target data should fail instead of returning a partial FX table."""
    usd_data = pd.DataFrame(
        {
            "armSkuName": ["SKU1"],
            "armRegionName": ["eastus"],
            "meterId": ["meter1"],
            "retailPrice": [10.0],
        }
    )

    def mock_get_prices(
        currency_code: str, results_filter: str = "", max_pages: int = 9999999
    ) -> pd.DataFrame:
        if currency_code == "USD":
            return usd_data.copy()
        if currency_code == "EUR":
            return pd.DataFrame(columns=usd_data.columns)
        raise AssertionError(f"Unexpected currency_code {currency_code}")

    monkeypatch.setattr(azureapi, "get_prices", mock_get_prices)

    with pytest.raises(ValueError, match="No prices found for target currency EUR"):
        azureapi.calculate_fx_rates(
            base_currency="USD",
            target_currencies=["EUR"],
            max_pages=1,
        )


def test_calculate_fx_rates_raises_for_missing_required_columns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FX rate calculation should fail with a descriptive error on malformed price data."""
    usd_data = pd.DataFrame(
        {
            "armSkuName": ["SKU1"],
            "armRegionName": ["eastus"],
            "retailPrice": [10.0],
        }
    )

    def mock_get_prices(
        currency_code: str, results_filter: str = "", max_pages: int = 9999999
    ) -> pd.DataFrame:
        assert currency_code == "USD"
        return usd_data.copy()

    monkeypatch.setattr(azureapi, "get_prices", mock_get_prices)

    with pytest.raises(ValueError, match="missing required columns: meterId"):
        azureapi.calculate_fx_rates(
            base_currency="USD",
            target_currencies=["EUR"],
            max_pages=1,
        )


@pytest.mark.live
@pytest.mark.skipif(
    not RUN_LIVE_AZURE_TESTS,
    reason="Set RUN_LIVE_AZURE_TESTS=1 to run live Azure smoke tests",
)
def test_live_get_price_data_smoke() -> None:
    """Live smoke test for the Azure Retail Prices API."""
    sku_list = azureapi.get_price_data(currency_code="USD", max_pages=1)

    assert isinstance(sku_list, list)
    assert len(sku_list) > 0
    assert isinstance(sku_list[0], dict)
    assert "retailPrice" in sku_list[0]


@pytest.mark.live
@pytest.mark.skipif(
    not RUN_LIVE_AZURE_TESTS,
    reason="Set RUN_LIVE_AZURE_TESTS=1 to run live Azure smoke tests",
)
def test_live_calculate_fx_rates_smoke() -> None:
    """Live smoke test for FX rate calculation."""
    fx_df = azureapi.calculate_fx_rates(
        base_currency="USD",
        target_currencies=["EUR"],
        results_filter="$filter=meterId eq '5daea80f-04ac-5385-86f0-b263d23becd2'",
        max_pages=1,
    )

    assert isinstance(fx_df, pd.DataFrame)
    assert len(fx_df) == 1
    assert fx_df.iloc[0]["currency"] == "EUR"
    assert fx_df.iloc[0]["fxRate"] > 0
