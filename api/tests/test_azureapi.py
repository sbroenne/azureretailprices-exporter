""" Unit tests for azureapi.py
"""

from api import azureapi
import pandas as pd

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
