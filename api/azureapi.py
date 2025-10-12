"""Azure Retail Prices API

This module provides functions to fetch and process Azure retail pricing data.
"""

import logging
import os
from datetime import timedelta
from typing import Any, cast

import enlighten  # pyright: ignore[reportMissingTypeStubs]
import pandas as pd
import requests
import requests_cache

# Configure logging
logger = logging.getLogger(__name__)

# Configuration from environment variables
API_VERSION = os.getenv("AZURE_PRICE_API_VERSION", "2023-01-01-preview")
CACHE_EXPIRE_DAYS = int(os.getenv("CACHE_EXPIRE_DAYS", "1"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))


def get_price_data(
    currency_code: str, results_filter: str = "", max_pages: int = 9999999
) -> list[dict[str, Any]]:
    """Download price data from the Azure Retail Price API

    Args:
        currency_code (str): Price currency
        results_filter (str, optional): Filter results string. Defaults to "".
            Examples: https://docs.microsoft.com/en-us/rest/api/
                     cost-management/retail-prices/azure-retail-prices
        max_pages (int, optional): Only download max_pages of results -
            useful for debugging. Defaults to 9999999.

    Returns:
        List[Dict[str, Any]]: Retail prices as a list of dictionaries
    """

    # Use requests_cache to temporarily cache results for one day
    # Useful if the script stops unexpectedly and you need to resume
    # Cast the cached session to requests.Session for type safety
    session = cast(
        requests.Session,
        requests_cache.CachedSession(
            "azure_cache", expire_after=timedelta(days=CACHE_EXPIRE_DAYS)
        ),
    )

    # Construct the base API url with configurable API version
    base_url = "https://prices.azure.com/api/retail/prices"
    api_url = (
        f"{base_url}?api-version={API_VERSION}" f"&currencyCode='{currency_code}''"
    )

    # Add optional filter argument
    if results_filter:
        api_url = f"{api_url}&{results_filter}"

    sku_list: list[dict[str, Any]] = []

    next_page_link: str | None = api_url

    logger.info("Starting export for API call: %s", api_url)
    page_counter = 0

    # Create progress counter only if we have a proper terminal
    counter: Any | None = None
    try:
        counter = enlighten.Counter(desc="Exported results:", unit="pages")
    except (OSError, AttributeError):
        # Fall back to no progress bar in test environments
        logger.debug("Progress bar not available, continuing without it")

    # Loop through the result pages
    while next_page_link and page_counter < max_pages:
        page_counter += 1

        try:
            # Get the next page with timeout and error handling
            api_request = session.get(next_page_link, timeout=REQUEST_TIMEOUT)
            api_request.raise_for_status()  # Raise exception for HTTP errors
            result_json = api_request.json()
        except requests.RequestException as e:
            logger.error("API request failed for page %d: %s", page_counter, e)
            raise
        except ValueError as e:
            logger.error("Failed to parse JSON response: %s", e)
            raise

        # Convert JSON results to list of dictionaries for pandas
        for sku_item in result_json["Items"]:
            sku_list.append(sku_item)

        next_page_link = result_json.get("NextPageLink")
        if counter:
            counter.update()  # pyright: ignore[reportUnknownMemberType]

    logger.info("Completed export of %d result pages", page_counter)

    return sku_list


def get_prices(
    currency_code: str, results_filter: str = "", max_pages: int = 9999999
) -> pd.DataFrame:
    """Download prices from the Azure API and transform savingsPlan data

    Args:
        currency_code (str): Price currency
        results_filter (str, optional): Filter results string. Defaults to "".
        max_pages (int, optional): Only download max_pages of results.
            Defaults to 9999999.

    Returns:
        pd.DataFrame: Retail prices as a Pandas data frame
    """

    input_records = get_price_data(
        currency_code=currency_code, results_filter=results_filter, max_pages=max_pages
    )

    # Transform the savingsPlan element and create a new dictionary
    output_records: list[dict[str, Any]] = []

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

    # pyright: ignore[reportUnknownMemberType]
    output_df = pd.DataFrame.from_records(output_records)
    logger.info("Created %d price items", output_df.shape[0])
    return output_df
