""" Azure Retail Prices API
"""
from datetime import timedelta

import enlighten
import pandas as pd
import requests_cache


def get_price_data(
    currency_code: str, results_filter: str = "", max_pages: int = 9999999
) -> list:
    """Download price data from the Azure Retail Price API

    Args:
        currency_code (str): Price currency
        results_filter (str, optional): Filter results string. Defaults to "". [Examples](https://docs.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices)
        max_pages (int, optional): Only download max_pages of results - only really useful for debugging.  Defaults to 9999999.

    Returns:
        [str]: Name of the exported file
        [list]: Retails prices as a list of dictionaries
    """

    # Use requests_cache to temporarily cache results for one day
    # Useful if the script stops unexpectedly and you need to resume
    session = requests_cache.CachedSession(
        "azure_cache", expire_after=timedelta(days=1)
    )

    # Construct the base API url
    api_url = f"https://prices.azure.com/api/retail/prices?api-version=2023-01-01-preview&currencyCode='{currency_code}''"

    # Add optional filter argument
    if len(results_filter) > 0:
        api_url = f"{api_url}&{results_filter}"

    sku_list = []

    next_page_link = api_url

    print(f"Starting export for API call: {api_url}")
    page_counter = 0

    counter = enlighten.Counter(desc="Exported results:", unit="pages")

    # Loop through the result pages
    while next_page_link is not None and page_counter < max_pages:
        page_counter = page_counter + 1

        # Get the next page
        api_request = session.get(next_page_link)
        result_json = api_request.json()

        # Convert the JSON results in a list of dictionaries that can be used by pandas
        for sku_item in result_json["Items"]:
            sku_list.append(sku_item)

        next_page_link = result_json["NextPageLink"]
        counter.update()

    print(f"Completed export of {page_counter} result pages")

    return sku_list


def get_prices(
    currency_code: str, results_filter: str = "", max_pages: int = 9999999
) -> pd.DataFrame:
    """
    Download prices from the Azure API and creates the price list by transforming the savingsPlan element

    Args:
        currency_code (str): Price currency
        results_filter (str, optional): Filter results string. Defaults to "". [Examples](https://docs.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices)
        max_pages (int, optional): Only download max_pages of results - only really useful for debugging.  Defaults to 9999999.

    Returns:
        [str]: Name of the exported file
        [pd.DataFrame]: Retails prices as a Pandas data frame
    """

    input_records = get_price_data(
        currency_code=currency_code, results_filter=results_filter, max_pages=max_pages
    )

    # Transform the savingsPlan element and create a new dictionary
    output_records = []

    for input_record in input_records:
        if "savingsPlan" in input_record:
            # Transform the savingsPlans node
            savingsPlans = input_record["savingsPlan"]
            for sp_year in savingsPlans:
                output_record = input_record.copy()
                output_record["type"] = "SavingsPlans"
                output_record["unitPrice"] = sp_year["unitPrice"]
                output_record["retailPrice"] = sp_year["retailPrice"]
                output_record["reservationTerm"] = sp_year["term"]
                del output_record["savingsPlan"]
                output_records.append(output_record)
        else:
            # Just append the original record
            output_records.append(input_record)

    output_df = pd.DataFrame.from_records(output_records)
    print(f"Created {output_df.shape[0]} price items")
    return output_df
