"""Regression tests for complete exports beyond Azure's skip limit."""

from copy import deepcopy
from typing import Any
from unittest.mock import Mock

import pytest

from api import azureapi

BOUNDARY = "https://prices.azure.com/api/retail/prices?$skip=1000000"


def page(records: list[dict[str, Any]], next_link: str | None = None) -> Mock:
    return Mock(**{"json.return_value": {"Items": records, "NextPageLink": next_link}})


@pytest.fixture
def session(monkeypatch: pytest.MonkeyPatch) -> Mock:
    mock = Mock()
    monkeypatch.setattr(azureapi, "_get_session", lambda: mock)
    monkeypatch.setattr(azureapi.enlighten, "Counter", lambda **kwargs: None)
    return mock


def test_overflow_restarts_disjoint_queries_without_duplicate_rows(
    session: Mock,
) -> None:
    compute = {"serviceFamily": "Compute", "meterId": "one"}
    storage = {"serviceFamily": "Storage", "meterId": "two"}
    records = [compute, storage]
    original = deepcopy(records)
    session.get.side_effect = [
        page(records, BOUNDARY),
        page([compute]),
        page([storage]),
    ]
    result = azureapi.get_price_data(
        "EUR", results_filter="$filter=priceType eq 'Consumption'"
    )
    assert result == records
    assert records == original
    calls = session.get.call_args_list
    assert len(calls) == 3
    left, right = [call.kwargs["params"] for call in calls[1:]]
    assert (
        left["$filter"]
        == "(priceType eq 'Consumption') and (serviceFamily eq 'Compute')"
    )
    assert (
        right["$filter"]
        == "(priceType eq 'Consumption') and (serviceFamily ne 'Compute')"
    )
    for call in calls:
        assert call.args[0] != BOUNDARY
        assert call.kwargs["params"]["currencyCode"] == "'EUR'"
        assert call.kwargs["params"]["api-version"] == azureapi.API_VERSION


def test_overflow_recurses_when_a_partition_is_still_too_large(session: Mock) -> None:
    east = {"serviceFamily": "Compute", "armRegionName": "eastus", "meterId": "one"}
    west = {"serviceFamily": "Compute", "armRegionName": "westus", "meterId": "two"}
    storage = {
        "serviceFamily": "Storage",
        "armRegionName": "eastus",
        "meterId": "three",
    }
    other_storage = {**storage, "meterId": "four"}
    session.get.side_effect = [
        page([east, west, storage, other_storage], BOUNDARY),
        page([east, west], BOUNDARY),
        page([east]),
        page([west]),
        page([storage, other_storage]),
    ]
    assert azureapi.get_price_data("USD") == [east, west, storage, other_storage]
    filters = [
        call.kwargs["params"]["$filter"] for call in session.get.call_args_list[1:]
    ]
    assert filters == [
        "serviceFamily eq 'Compute'",
        "(serviceFamily eq 'Compute') and (armRegionName eq 'eastus')",
        "(serviceFamily eq 'Compute') and (armRegionName ne 'eastus')",
        "serviceFamily ne 'Compute'",
    ]


@pytest.mark.parametrize("max_pages", [0, 1, 2])
def test_page_budget_applies_across_partition_restarts(
    session: Mock, max_pages: int
) -> None:
    records = [{"meterId": "one"}, {"meterId": "two"}]
    session.get.side_effect = [
        page(records, BOUNDARY),
        page([records[0]]),
        page([records[1]]),
    ]
    result = azureapi.get_price_data("USD", max_pages=max_pages)
    assert session.get.call_count == max_pages
    assert result == {0: [], 1: records, 2: records[:1]}[max_pages]


def test_partition_failure_never_returns_a_partial_export(session: Mock) -> None:
    session.get.side_effect = [
        page([{"meterId": "one"}, {"meterId": "two"}], BOUNDARY),
        page([{"meterId": "one"}]),
        RuntimeError("second partition failed"),
    ]
    with pytest.raises(RuntimeError, match="second partition"):
        azureapi.get_price_data("USD")


def test_unsplittable_overflow_fails_instead_of_truncating(session: Mock) -> None:
    session.get.return_value = page([{"meterId": "one"}], BOUNDARY)
    with pytest.raises(ValueError, match="Cannot safely partition"):
        azureapi.get_price_data("USD")
    assert session.get.call_count == 1


def test_partition_filters_escape_values_and_preserve_query_options() -> None:
    left, right = azureapi._partition_price_query(
        {"currencyCode": "'USD'", "$top": "1000"},
        [{"serviceName": "O'Brien"}, {"serviceName": "Other"}],
    )
    assert left["$filter"] == "serviceName eq 'O''Brien'"
    assert right["$filter"] == "serviceName ne 'O''Brien'"
    assert left["$top"] == right["$top"] == "1000"


def test_partition_can_balance_several_values_without_a_static_catalog() -> None:
    left, right = azureapi._partition_price_query(
        {}, [{"serviceFamily": value} for value in ["A", "B", "C", "D"]]
    )
    assert left["$filter"] == "serviceFamily eq 'A' or serviceFamily eq 'B'"
    assert right["$filter"] == "serviceFamily ne 'A' and serviceFamily ne 'B'"


def test_initial_offset_cannot_silently_skip_rows_in_each_partition() -> None:
    with pytest.raises(ValueError, match="initial \\$skip"):
        azureapi._partition_price_query(
            {"$skip": "100"}, [{"meterId": "one"}, {"meterId": "two"}]
        )
