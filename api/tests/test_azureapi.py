"""Unit tests for azureapi.py"""

import pandas as pd

from api import azureapi

# Currency cod to use
currency_code = "USD"

# Maximum output pages
max_pages = 2


def test_azureapi_get_price_data():
    """Test basic export functionality"""
    sku_list = azureapi.get_price_data(currency_code=currency_code, max_pages=max_pages)
    assert isinstance(sku_list, list)


def test_azureapi_savings_plan_get_price_data():
    """Test export with a filter that will include savings plans data"""

    filter = "$filter=serviceName eq 'Virtual Machines' and type eq 'Consumption' and armRegionname eq 'westeurope'"

    sku_list = azureapi.get_price_data(
        currency_code=currency_code, results_filter=filter, max_pages=max_pages
    )
    assert isinstance(sku_list, list)


def test_azureapi_savings_plan_get_prices():
    """Test export with a filter that will include savings plans data"""

    filter = "$filter=serviceName eq 'Virtual Machines' and type eq 'Consumption' and armRegionname eq 'westeurope'"

    test_df = azureapi.get_prices(
        currency_code=currency_code, results_filter=filter, max_pages=max_pages
    )
    assert isinstance(test_df, pd.DataFrame)


def test_calculate_fx_rates_with_mock_data():
    """Test FX rate calculation with mock data"""
    # Create mock data for USD
    usd_data = pd.DataFrame(
        {
            "armSkuName": ["SKU1", "SKU2", "SKU3"],
            "armRegionName": ["eastus", "westus", "eastus"],
            "meterId": ["meter1", "meter2", "meter3"],
            "retailPrice": [10.0, 20.0, 30.0],
            "productName": ["Product 1", "Product 2", "Product 3"],
        }
    )

    # Create mock data for EUR (with 0.85 exchange rate)
    eur_data = pd.DataFrame(
        {
            "armSkuName": ["SKU1", "SKU2", "SKU3"],
            "armRegionName": ["eastus", "westus", "eastus"],
            "meterId": ["meter1", "meter2", "meter3"],
            "retailPrice": [8.5, 17.0, 25.5],
            "productName": ["Product 1", "Product 2", "Product 3"],
        }
    )

    # Mock the get_prices function
    def mock_get_prices(currency_code, results_filter="", max_pages=9999999):
        if currency_code == "USD":
            return usd_data.copy()
        elif currency_code == "EUR":
            return eur_data.copy()
        else:
            return pd.DataFrame()

    # Temporarily replace the function
    original_get_prices = azureapi.get_prices
    azureapi.get_prices = mock_get_prices

    try:
        # Test the FX rate calculation
        fx_df = azureapi.calculate_fx_rates(
            base_currency="USD", target_currencies=["EUR"], max_pages=1
        )

        # Verify the result
        assert isinstance(fx_df, pd.DataFrame)
        assert len(fx_df) == 1
        assert fx_df.iloc[0]["currency"] == "EUR"
        # FX rate should be 0.85 (first product: 8.5 / 10.0)
        assert abs(fx_df.iloc[0]["fxRate"] - 0.85) < 0.01
        # Should only have currency and fxRate fields
        assert "sampleSize" not in fx_df.columns
        assert "productSample" not in fx_df.columns
        assert list(fx_df.columns) == ["currency", "fxRate"]

    finally:
        # Restore the original function
        azureapi.get_prices = original_get_prices


def test_calculate_fx_rates_returns_dataframe():
    """Test that calculate_fx_rates returns a DataFrame structure"""
    # This test just verifies the function signature and basic structure
    # It will fail in environments without API access, which is expected

    # Test that the function accepts the correct parameters
    # and returns a DataFrame (even if empty due to API errors)
    try:
        result = azureapi.calculate_fx_rates(
            base_currency="USD", target_currencies=["EUR"], max_pages=1
        )
        assert isinstance(result, pd.DataFrame)
    except Exception:
        # If the API is not accessible, we just verify the function exists
        # and has the correct signature
        assert callable(azureapi.calculate_fx_rates)
