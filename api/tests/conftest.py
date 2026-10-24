"""Shared Azure API test data."""

from collections.abc import Iterator
from typing import Any

import pytest

from api import azureapi


@pytest.fixture(autouse=True)
def isolate_http_session(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Isolate the lazy HTTP session and close it after each test."""
    monkeypatch.setattr(azureapi, "_session", None)
    yield
    if azureapi._session is not None:
        azureapi._session.close()


@pytest.fixture
def price_record() -> dict[str, Any]:
    """Return a representative parent price with a complete identity."""
    return {
        "currencyCode": "USD",
        "armSkuName": "Standard_D2s_v5",
        "armRegionName": "eastus",
        "skuId": "DZH318Z08M9W/0061",
        "meterId": "36cc2454-47d7-517f-884f-be4d6b7efa55",
        "productName": "Virtual Machines Dsv5 Series",
        "type": "Consumption",
        "tierMinimumUnits": 0,
        "unitOfMeasure": "1 Hour",
        "unitPrice": 0.096,
        "retailPrice": 0.096,
        "effectiveStartDate": "2021-11-01T00:00:00Z",
    }
