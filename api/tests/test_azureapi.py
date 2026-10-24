"""Deterministic tests for API requests, retries, price expansion, and CSV output."""

import json
from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import StringIO
from threading import Thread
from typing import Any
from unittest.mock import Mock, patch

import pandas as pd
import pytest
import requests

from api import azureapi


def test_get_price_data_passes_currency_filter_and_timeout(
    price_record: dict[str, Any],
) -> None:
    record = {**price_record, "currencyCode": "EUR"}
    session = Mock()
    session.get.return_value.json.return_value = {
        "Items": [record],
        "NextPageLink": None,
    }
    query = "$filter=meterId eq 'test-meter'"
    with (
        patch.object(azureapi.requests_cache, "CachedSession", return_value=session),
        patch.object(azureapi.enlighten, "Counter", return_value=None),
    ):
        result = azureapi.get_price_data("EUR", results_filter=query, max_pages=1)

    assert result == [record]
    session.get.assert_called_once_with(
        "https://prices.azure.com/api/retail/prices",
        params={
            "api-version": azureapi.API_VERSION,
            "currencyCode": "'EUR'",
            "$filter": "meterId eq 'test-meter'",
        },
        timeout=azureapi.REQUEST_TIMEOUT,
    )
    assert session.mount.call_count == 2
    retry = session.mount.call_args.args[1].max_retries
    assert retry.total == azureapi.MAX_RETRIES
    assert 429 in retry.status_forcelist
    assert retry.respect_retry_after_header


def test_get_prices_preserves_parent_and_expands_savings_plans(
    price_record: dict[str, Any],
) -> None:
    plans = [
        {"unitPrice": 0.0658368, "retailPrice": 0.0658368, "term": "1 Year"},
        {"unitPrice": 0.0441792, "retailPrice": 0.0441792, "term": "3 Years"},
    ]
    records = [{**price_record, "savingsPlan": plans}]
    original = deepcopy(records)
    expected = [
        price_record,
        {
            **price_record,
            "type": "SavingsPlans",
            "unitPrice": 0.0658368,
            "retailPrice": 0.0658368,
            "reservationTerm": "1 Year",
        },
        {
            **price_record,
            "type": "SavingsPlans",
            "unitPrice": 0.0441792,
            "retailPrice": 0.0441792,
            "reservationTerm": "3 Years",
        },
    ]
    with patch.object(
        azureapi, "get_price_data", return_value=records
    ) as mock_get_price_data:
        result = azureapi.get_prices(
            "USD", results_filter="$filter=type eq 'Consumption'", max_pages=1
        )

    mock_get_price_data.assert_called_once_with(
        currency_code="USD", results_filter="$filter=type eq 'Consumption'", max_pages=1
    )
    pd.testing.assert_frame_equal(result, pd.DataFrame.from_records(expected))
    assert "savingsPlan" not in result.columns
    assert records == original


@pytest.mark.parametrize("savings_plan_fields", [{}, {"savingsPlan": []}])
@pytest.mark.parametrize(
    "price_type", ["Consumption", "Reservation", "DevTestConsumption"]
)
def test_get_prices_preserves_parent_without_plans(
    price_record: dict[str, Any],
    savings_plan_fields: dict[str, Any],
    price_type: str,
) -> None:
    parent = {**price_record, "type": price_type}
    records = [{**parent, **savings_plan_fields}]
    original = deepcopy(records)
    with patch.object(azureapi, "get_price_data", return_value=records):
        result = azureapi.get_prices("USD")

    pd.testing.assert_frame_equal(result, pd.DataFrame.from_records([parent]))
    assert "savingsPlan" not in result.columns
    assert records == original


def test_get_prices_exports_paginated_api_records_to_csv(
    price_record: dict[str, Any],
) -> None:
    next_page = "https://prices.azure.com/api/retail/prices?next=2"
    plans = [
        {"unitPrice": 0.0658368, "retailPrice": 0.0658368, "term": "1 Year"},
        {"unitPrice": 0.0441792, "retailPrice": 0.0441792, "term": "3 Years"},
    ]
    pages = [
        {"Items": [{**price_record, "savingsPlan": plans}], "NextPageLink": next_page},
        {
            "Items": [
                {**price_record, "meterId": "without-plans"},
                {**price_record, "meterId": "empty-plans", "savingsPlan": []},
            ],
            "NextPageLink": None,
        },
    ]
    original = deepcopy(pages)
    session = Mock()
    session.get.side_effect = [Mock(**{"json.return_value": page}) for page in pages]
    with (
        patch.object(azureapi.requests_cache, "CachedSession", return_value=session),
        patch.object(azureapi.enlighten, "Counter", return_value=None),
    ):
        result = azureapi.get_prices("USD", max_pages=2)

    exported = pd.read_csv(StringIO(result.to_csv(index=False)))
    pd.testing.assert_frame_equal(exported, result)
    assert exported["type"].tolist() == [
        "Consumption",
        "SavingsPlans",
        "SavingsPlans",
        "Consumption",
        "Consumption",
    ]
    assert exported["retailPrice"].tolist() == [
        0.096,
        0.0658368,
        0.0441792,
        0.096,
        0.096,
    ]
    assert exported["unitPrice"].tolist() == exported["retailPrice"].tolist()
    assert exported["reservationTerm"].dropna().tolist() == ["1 Year", "3 Years"]
    assert "savingsPlan" not in exported.columns
    assert pages == original
    assert session.get.call_count == 2
    session.get.assert_called_with(
        next_page, params=None, timeout=azureapi.REQUEST_TIMEOUT
    )


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {},
        {"Items": {}},
        {"Items": ["not-an-object"]},
        {"Items": [], "NextPageLink": 123},
    ],
)
def test_get_price_data_rejects_malformed_responses(payload: Any) -> None:
    session = Mock()
    session.get.return_value.json.return_value = payload
    with (
        patch.object(azureapi.requests_cache, "CachedSession", return_value=session),
        patch.object(azureapi.enlighten, "Counter", return_value=None),
        pytest.raises(ValueError),
    ):
        azureapi.get_price_data("USD", max_pages=1)


def test_get_price_data_reuses_the_http_session() -> None:
    session = Mock()
    session.get.return_value.json.return_value = {"Items": [], "NextPageLink": None}
    with (
        patch.object(
            azureapi.requests_cache, "CachedSession", return_value=session
        ) as factory,
        patch.object(azureapi.enlighten, "Counter", return_value=None),
    ):
        assert azureapi.get_price_data("USD", max_pages=1) == []
        assert azureapi.get_price_data("EUR", max_pages=1) == []
    factory.assert_called_once()
    assert session.mount.call_count == 2


def test_get_price_data_honors_page_limit(price_record: dict[str, Any]) -> None:
    session = Mock()
    session.get.return_value.json.return_value = {
        "Items": [price_record],
        "NextPageLink": "https://prices.azure.com/next",
    }
    with (
        patch.object(azureapi.requests_cache, "CachedSession", return_value=session),
        patch.object(azureapi.enlighten, "Counter", return_value=None),
    ):
        assert azureapi.get_price_data("USD", max_pages=1) == [price_record]
    assert session.get.call_count == 1


@pytest.mark.parametrize(
    "error", [requests.HTTPError("failed"), ValueError("bad JSON")]
)
def test_get_price_data_propagates_errors(error: Exception) -> None:
    session = Mock()
    if isinstance(error, requests.HTTPError):
        session.get.return_value.raise_for_status.side_effect = error
    else:
        session.get.return_value.json.side_effect = error
    with (
        patch.object(azureapi.requests_cache, "CachedSession", return_value=session),
        patch.object(azureapi.enlighten, "Counter", return_value=None),
        pytest.raises(type(error)),
    ):
        azureapi.get_price_data("USD", max_pages=1)


@pytest.mark.parametrize("retries, succeeds", [(2, True), (1, False)])
def test_http_429_retry_handling(
    price_record: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    retries: int,
    succeeds: bool,
) -> None:
    attempts: list[int] = []
    body = json.dumps({"Items": [price_record], "NextPageLink": None}).encode()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            attempts.append(1)
            self.send_response(429 if len(attempts) <= 2 else 200)
            self.send_header("Retry-After", "0")
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    monkeypatch.setattr(azureapi, "MAX_RETRIES", retries)
    monkeypatch.setattr(azureapi, "RETRY_BACKOFF_FACTOR", 0)
    try:
        with requests.Session() as session:
            original_get = session.get

            def local_get(url: str, **kwargs: Any) -> requests.Response:
                return original_get(f"http://127.0.0.1:{server.server_port}", **kwargs)

            with (
                patch.object(
                    azureapi.requests_cache, "CachedSession", return_value=session
                ),
                patch.object(azureapi.enlighten, "Counter", return_value=None),
                patch.object(session, "get", side_effect=local_get),
            ):
                if succeeds:
                    assert azureapi.get_price_data("USD", max_pages=1) == [price_record]
                else:
                    with pytest.raises(requests.exceptions.RetryError):
                        azureapi.get_price_data("USD", max_pages=1)
        assert len(attempts) == retries + 1
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
    assert not worker.is_alive()
