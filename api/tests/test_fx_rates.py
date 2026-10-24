"""FX matching, failure handling, and export-boundary regression tests."""

import sys
from copy import deepcopy
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pandas as pd
import pytest
import requests

import export_fxrates
from api import azureapi


def test_fx_matches_shuffled_terms_and_tiers(price_record: dict[str, Any]) -> None:
    identities = [
        {
            "skuId": "reservation-one",
            "type": "Reservation",
            "reservationTerm": "1 Year",
        },
        {
            "skuId": "reservation-three",
            "type": "Reservation",
            "reservationTerm": "3 Years",
        },
        {"type": "SavingsPlans", "reservationTerm": "1 Year"},
        {"type": "SavingsPlans", "reservationTerm": "3 Years"},
        {"tierMinimumUnits": 100},
        {},
    ]
    usd = pd.DataFrame(
        [
            {**price_record, **identity, "retailPrice": (index + 1) * 100.0}
            for index, identity in enumerate(identities)
        ]
    )
    eur = usd.iloc[::-1].copy()
    eur["currencyCode"] = "EUR"
    eur["retailPrice"] *= 0.9
    original_usd, original_eur = deepcopy(usd), deepcopy(eur)
    with patch.object(azureapi, "get_prices", side_effect=[usd, eur]) as get_prices:
        result = azureapi.calculate_fx_rates(
            target_currencies=["EUR"],
            results_filter="$filter=meterId eq 'test'",
            max_pages=1,
        )
    assert result.to_dict("records") == [{"currency": "EUR", "fxRate": 0.9}]
    assert get_prices.call_args.kwargs["results_filter"] == "$filter=meterId eq 'test'"
    assert get_prices.call_args.kwargs["max_pages"] == 1
    pd.testing.assert_frame_equal(usd, original_usd)
    pd.testing.assert_frame_equal(eur, original_eur)


@pytest.mark.parametrize("currency", ["USD", "EUR"])
def test_fx_rejects_duplicate_identities(
    price_record: dict[str, Any], currency: str
) -> None:
    usd = pd.DataFrame([price_record])
    eur = pd.DataFrame([{**price_record, "currencyCode": "EUR"}])
    if currency == "USD":
        usd = pd.concat([usd, usd], ignore_index=True)
    else:
        eur = pd.concat([eur, eur], ignore_index=True)
    with (
        patch.object(azureapi, "get_prices", side_effect=[usd, eur]),
        pytest.raises(ValueError, match="Ambiguous"),
    ):
        azureapi.calculate_fx_rates(target_currencies=["EUR"])


@pytest.mark.parametrize(
    "bad_data",
    [
        pd.DataFrame(),
        pd.DataFrame({"retailPrice": [10.0]}),
    ],
)
def test_fx_rejects_missing_base_data(bad_data: pd.DataFrame) -> None:
    with (
        patch.object(azureapi, "get_prices", return_value=bad_data),
        pytest.raises(ValueError, match="Missing"),
    ):
        azureapi.calculate_fx_rates(target_currencies=["EUR"])


@pytest.mark.parametrize("currency", ["USD", "EUR"])
def test_fx_rejects_missing_identity_values(
    price_record: dict[str, Any], currency: str
) -> None:
    usd = pd.DataFrame([price_record])
    eur = pd.DataFrame([{**price_record, "currencyCode": "EUR"}])
    (usd if currency == "USD" else eur)["skuId"] = None
    with (
        patch.object(azureapi, "get_prices", side_effect=[usd, eur]),
        pytest.raises(ValueError, match="Missing price identity values"),
    ):
        azureapi.calculate_fx_rates(target_currencies=["EUR"])


@pytest.mark.parametrize("failure", ["timeout", "empty", "wrong-currency", "unmatched"])
def test_fx_never_returns_partial_results(
    price_record: dict[str, Any], failure: str
) -> None:
    usd = pd.DataFrame([price_record])
    eur = pd.DataFrame([{**price_record, "currencyCode": "EUR"}])
    invalid: Any = {
        "timeout": requests.Timeout("failed"),
        "empty": pd.DataFrame(),
        "wrong-currency": usd,
        "unmatched": pd.DataFrame(
            [{**price_record, "currencyCode": "GBP", "skuId": "different"}]
        ),
    }[failure]
    with (
        patch.object(azureapi, "get_prices", side_effect=[usd, eur, invalid]),
        pytest.raises(requests.Timeout if failure == "timeout" else ValueError),
    ):
        azureapi.calculate_fx_rates(target_currencies=["EUR", "GBP"])


@pytest.mark.parametrize("price", [0, -1, float("nan"), float("inf")])
def test_fx_rejects_invalid_matching_prices(
    price_record: dict[str, Any], price: float
) -> None:
    usd = pd.DataFrame([price_record])
    eur = pd.DataFrame([{**price_record, "currencyCode": "EUR", "retailPrice": price}])
    with (
        patch.object(azureapi, "get_prices", side_effect=[usd, eur]),
        pytest.raises(ValueError, match="No positive"),
    ):
        azureapi.calculate_fx_rates(target_currencies=["EUR"])


def test_fx_skips_free_prices_when_a_paid_match_exists(
    price_record: dict[str, Any],
) -> None:
    usd = pd.DataFrame(
        [
            {**price_record, "skuId": "free", "retailPrice": 0.0},
            {**price_record, "skuId": "paid", "retailPrice": 100.0},
        ]
    )
    eur = usd.copy()
    eur["currencyCode"] = "EUR"
    eur["retailPrice"] *= 0.9
    with patch.object(azureapi, "get_prices", side_effect=[usd, eur]):
        result = azureapi.calculate_fx_rates(target_currencies=["EUR"])
    assert result.to_dict("records") == [{"currency": "EUR", "fxRate": 0.9}]


def test_fx_empty_targets_keep_schema_without_requesting_prices() -> None:
    with patch.object(azureapi, "get_prices") as get_prices:
        result = azureapi.calculate_fx_rates(target_currencies=[])
    assert result.empty
    assert list(result.columns) == ["currency", "fxRate"]
    get_prices.assert_not_called()


def test_fx_rejects_duplicate_targets() -> None:
    with pytest.raises(ValueError, match="unique"):
        azureapi.calculate_fx_rates(target_currencies=["EUR", "EUR"])


@pytest.mark.parametrize(
    "records, columns",
    [
        ([], []),
        ([], ["currency", "fxRate"]),
        ([{"currency": "GBP", "fxRate": 0.9}], ["currency", "fxRate"]),
        ([{"currency": "EUR", "fxRate": 0.9}] * 2, ["currency", "fxRate"]),
        ([{"currency": "EUR", "fxRate": 0}], ["currency", "fxRate"]),
        ([{"currency": "EUR", "fxRate": float("nan")}], ["currency", "fxRate"]),
        ([{"currency": "EUR", "fxRate": float("inf")}], ["currency", "fxRate"]),
    ],
)
def test_fx_validation_rejects_incomplete_or_invalid_output(
    records: list[dict[str, Any]], columns: list[str]
) -> None:
    with pytest.raises(ValueError):
        azureapi.validate_fx_rates(pd.DataFrame(records, columns=columns), ["EUR"])


def test_fx_export_does_not_overwrite_file_on_incomplete_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "fx.csv"
    output.write_text("previous valid data", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["export_fxrates.py", "--output", str(output)])
    with (
        patch.object(azureapi, "calculate_fx_rates", return_value=pd.DataFrame()),
        pytest.raises(ValueError),
    ):
        export_fxrates.main()
    assert output.read_text(encoding="utf-8") == "previous valid data"


def test_fx_export_writes_every_required_currency(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "fx.csv"
    expected = pd.DataFrame(
        {
            "currency": export_fxrates.TARGET_CURRENCIES,
            "fxRate": [0.9] * len(export_fxrates.TARGET_CURRENCIES),
        }
    )
    monkeypatch.setattr(sys, "argv", ["export_fxrates.py", "--output", str(output)])
    with patch.object(azureapi, "calculate_fx_rates", return_value=expected):
        export_fxrates.main()
    pd.testing.assert_frame_equal(pd.read_csv(output), expected)
