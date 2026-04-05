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
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logger = logging.getLogger(__name__)

# Configuration from environment variables
API_VERSION = os.getenv("AZURE_PRICE_API_VERSION", "2023-01-01-preview")
CACHE_EXPIRE_DAYS = int(os.getenv("CACHE_EXPIRE_DAYS", "1"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

# Retry configuration for handling rate limiting (HTTP 429)
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))
RETRY_BACKOFF_FACTOR = float(os.getenv("RETRY_BACKOFF_FACTOR", "2.0"))
RETRY_STATUS_FORCELIST = [429, 500, 502, 503, 504]  # HTTP status codes to retry

# Module-level cached session (lazily initialized to enable test patching)
_session: requests.Session | None = None


def _get_session() -> requests.Session:
    """Return the module-level cached HTTP session, creating it on first call.

    The session is created once and reused across all calls to avoid the
    overhead of opening a new SQLite cache connection on every request.
    """
    global _session
    if _session is None:
        cached = requests_cache.CachedSession(
            "azure_cache", expire_after=timedelta(days=CACHE_EXPIRE_DAYS)
        )
        retry_strategy = Retry(
            total=MAX_RETRIES,
            status_forcelist=RETRY_STATUS_FORCELIST,
            backoff_factor=RETRY_BACKOFF_FACTOR,
            respect_retry_after_header=True,
            allowed_methods=[
                "GET",
                "POST",
                "PUT",
                "DELETE",
                "HEAD",
                "OPTIONS",
                "TRACE",
            ],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        cached.mount("http://", adapter)
        cached.mount("https://", adapter)
        _session = cast(requests.Session, cached)
        logger.debug(
            "Created session: max_retries=%d, backoff_factor=%.1f, status_forcelist=%s",
            MAX_RETRIES,
            RETRY_BACKOFF_FACTOR,
            RETRY_STATUS_FORCELIST,
        )
    return _session


def _create_match_key(df: pd.DataFrame) -> pd.Series:  # type: ignore[type-arg]
    """Build a product match key from armSkuName, armRegionName, and meterId."""
    return (
        df["armSkuName"].astype(str)
        + "|"
        + df["armRegionName"].astype(str)
        + "|"
        + df["meterId"].astype(str)
    )


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

    session = _get_session()

    # Construct the base API url with configurable API version
    base_url = "https://prices.azure.com/api/retail/prices"
    api_url = f"{base_url}?api-version={API_VERSION}&currencyCode='{currency_code}'"

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


def calculate_fx_rates(
    base_currency: str = "USD",
    target_currencies: list[str] | None = None,
    results_filter: str = "",
    max_pages: int = 9999999,
) -> pd.DataFrame:
    """Calculate FX rates by comparing prices across currencies.

    This function fetches prices in multiple currencies and calculates exchange rates
    by comparing the same product prices across currencies. The base currency (default USD)
    is used as the reference. Since FX rates are the same across all products, only the
    first matched product is used for calculation.

    Args:
        base_currency (str, optional): Base currency for FX rates. Defaults to "USD".
        target_currencies (list[str] | None, optional): List of target currencies to compare.
            If None, uses a default list of common currencies.
        results_filter (str, optional): Filter results string. Defaults to "".
        max_pages (int, optional): Only download max_pages of results. Defaults to 9999999.

    Returns:
        pd.DataFrame: DataFrame with columns: currency, fxRate
    """
    if target_currencies is None:
        # Default list of common currencies
        target_currencies = ["EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR"]

    logger.info(
        "Calculating FX rates from %s to %s",
        base_currency,
        ", ".join(target_currencies),
    )

    # Get base currency prices
    logger.info("Fetching %s prices...", base_currency)
    base_df = get_prices(
        currency_code=base_currency,
        results_filter=results_filter,
        max_pages=max_pages,
    )

    # Check if we have data
    if len(base_df) == 0:
        logger.warning("No prices found for base currency %s", base_currency)
        return pd.DataFrame({"currency": [], "fxRate": []})

    # Use a unique key to match products across currencies
    base_df["matchKey"] = _create_match_key(base_df)

    fx_results: list[dict[str, Any]] = []

    for target_currency in target_currencies:
        try:
            logger.info("Fetching %s prices...", target_currency)
            target_df = get_prices(
                currency_code=target_currency,
                results_filter=results_filter,
                max_pages=max_pages,
            )

            # Check if we have data for target currency
            if len(target_df) == 0:
                logger.warning("No prices found for currency %s", target_currency)
                continue

            # Create match key for target currency
            target_df["matchKey"] = _create_match_key(target_df)

            # Merge on the match key to find common products
            merged_df = base_df.merge(
                target_df,
                on="matchKey",
                suffixes=("_base", "_target"),
                how="inner",
            )

            if len(merged_df) > 0:
                # Filter out records where either price is zero or null
                valid_df = merged_df[
                    (merged_df["retailPrice_base"] > 0)
                    & (merged_df["retailPrice_target"] > 0)
                    & (merged_df["retailPrice_base"].notna())
                    & (merged_df["retailPrice_target"].notna())
                ]

                if len(valid_df) > 0:
                    # Use first matched product - FX rates are the same across all products
                    first_row = valid_df.iloc[0]
                    fx_rate = (
                        first_row["retailPrice_target"] / first_row["retailPrice_base"]
                    )

                    fx_results.append(
                        {
                            "currency": target_currency,
                            "fxRate": fx_rate,
                        }
                    )

                    logger.info(
                        "Calculated FX rate for %s: %.4f",
                        target_currency,
                        fx_rate,
                    )
                else:
                    logger.warning(
                        "No valid price comparisons found for %s", target_currency
                    )
            else:
                logger.warning("No matching products found for %s", target_currency)

        except Exception as e:
            logger.error("Failed to calculate FX rate for %s: %s", target_currency, e)
            continue

    # Create DataFrame from results
    fx_df = pd.DataFrame.from_records(fx_results)
    logger.info("Calculated FX rates for %d currencies", len(fx_df))

    return fx_df
