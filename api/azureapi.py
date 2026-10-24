"""Azure Retail Prices API

This module provides functions to fetch and process Azure retail pricing data.
"""

import logging
import os
from collections import Counter
from datetime import timedelta
from typing import Any, cast
from urllib.parse import parse_qsl, urlsplit

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
MAX_API_SKIP = 1_000_000
FX_PRICE_IDENTITY = [
    "skuId",
    "armRegionName",
    "meterId",
    "type",
    "reservationTerm",
    "tierMinimumUnits",
    "unitOfMeasure",
]


def _build_initial_request_params(
    currency_code: str, results_filter: str
) -> dict[str, str]:
    """Build the initial request parameters for the Azure Retail Prices API."""
    params = {
        "api-version": API_VERSION,
        "currencyCode": f"'{currency_code}'",
    }

    if not results_filter:
        return params

    filter_params = dict(parse_qsl(results_filter.lstrip("?"), keep_blank_values=True))
    if not filter_params:
        raise ValueError(
            'results_filter must be a query string fragment like "$filter=..."'
        )

    params.update(filter_params)
    return params


def _extract_page_data(
    result_json: Any, page_counter: int
) -> tuple[list[dict[str, Any]], str | None]:
    """Validate and extract Azure API page data."""
    if not isinstance(result_json, dict):
        raise ValueError(
            f"Unexpected response type for page {page_counter}: "
            f"{type(result_json).__name__}"
        )

    items = result_json.get("Items")
    if not isinstance(items, list):
        raise ValueError(
            f"Azure API response for page {page_counter} did not contain a valid "
            f"'Items' list: {result_json}"
        )

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(
                f"Azure API response for page {page_counter} contained a non-object "
                f"item at index {index}: {item!r}"
            )

    next_page_link = result_json.get("NextPageLink")
    if next_page_link is not None and not isinstance(next_page_link, str):
        raise ValueError(
            f"Azure API response for page {page_counter} contained an invalid "
            f"'NextPageLink': {next_page_link!r}"
        )

    return items, next_page_link


def _partition_price_query(
    params: dict[str, str], records: list[dict[str, Any]]
) -> tuple[dict[str, str], dict[str, str]]:
    """Split an overflowing query into disjoint, exhaustive equality filters."""
    if int(params.get("$skip", "0") or "0") != 0:
        raise ValueError("Cannot safely partition a query with an initial $skip")
    best: tuple[int, str, list[str]] | None = None
    for field in (
        "serviceFamily",
        "serviceName",
        "armRegionName",
        "productId",
        "skuId",
        "meterId",
    ):
        counts: Counter[str] = Counter()
        for record in records:
            value = record.get(field)
            if isinstance(value, str):
                counts[value] += 1
        values = []
        matches = 0
        for value, count in counts.most_common(16):
            values.append(value)
            matches += count
            if 0 < matches < len(records):
                imbalance = abs(len(records) - 2 * matches)
                if best is None or imbalance < best[0]:
                    best = imbalance, field, values.copy()
            if matches * 2 >= len(records):
                break
        if best is not None and best[0] == 0:
            break
    if best is None:
        raise ValueError("Cannot safely partition prices at the Azure pagination limit")

    _, field, values = best
    escaped = [value.replace("'", "''") for value in values]
    positive = " or ".join(f"{field} eq '{value}'" for value in escaped)
    negative = " and ".join(f"{field} ne '{value}'" for value in escaped)
    original = params.get("$filter", "")
    partitions = []
    for condition in (positive, negative):
        partition = params.copy()
        partition["$filter"] = (
            f"({original}) and ({condition})" if original else condition
        )
        partitions.append(partition)
    return partitions[0], partitions[1]


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


def get_price_data(
    currency_code: str, results_filter: str = "", max_pages: int = 9999999
) -> list[dict[str, Any]]:
    """Download prices, partitioning queries that reach Azure's pagination limit.

    An overflowing query is restarted as complementary filtered queries; its
    partial pages are discarded so rows are neither duplicated nor truncated.
    The max_pages budget covers requests across all partitions.

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
    initial_request_params = _build_initial_request_params(
        currency_code, results_filter
    )

    prepared_request = requests.Request(
        "GET", base_url, params=initial_request_params
    ).prepare()
    logger.info("Starting export for API call: %s", prepared_request.url)
    page_counter = 0

    # Create progress counter only if we have a proper terminal
    counter: Any | None = None
    try:
        counter = enlighten.Counter(desc="Exported results:", unit="pages")
    except (OSError, AttributeError):
        # Fall back to no progress bar in test environments
        logger.debug("Progress bar not available, continuing without it")

    def fetch(params: dict[str, str]) -> list[dict[str, Any]]:
        nonlocal page_counter
        records: list[dict[str, Any]] = []
        next_page_link: str | None = base_url
        request_params: dict[str, str] | None = params
        while next_page_link and page_counter < max_pages:
            skip = dict(parse_qsl(urlsplit(next_page_link).query)).get("$skip", "0")
            if int(skip) >= MAX_API_SKIP:
                left, right = _partition_price_query(params, records)
                logger.info(
                    "Restarting overflowing price query as partitions: %s / %s",
                    left["$filter"],
                    right["$filter"],
                )
                records.clear()
                records.extend(fetch(left))
                records.extend(fetch(right))
                return records
            page_counter += 1
            try:
                response = session.get(
                    next_page_link, params=request_params, timeout=REQUEST_TIMEOUT
                )
                response.raise_for_status()
                result_json = response.json()
            except requests.RequestException as error:
                logger.error("API request failed for page %d: %s", page_counter, error)
                raise
            except ValueError as error:
                logger.error("Failed to parse JSON response: %s", error)
                raise
            items, next_page_link = _extract_page_data(result_json, page_counter)
            records.extend(items)
            request_params = None
            if counter:
                counter.update()
        return records

    try:
        sku_list = fetch(initial_request_params)
    finally:
        if counter:
            counter.close()
    logger.info("Completed export of %d result pages", page_counter)
    return sku_list


def get_prices(
    currency_code: str, results_filter: str = "", max_pages: int = 9999999
) -> pd.DataFrame:
    """Download prices, preserving parents and expanding savingsPlan data.

    Each parent is retained without its nested savingsPlan field. Each plan
    becomes an additional SavingsPlans row with its own prices and term.
    Other fields, including dates, are copied from the parent; the input
    records are not modified.

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

    output_records: list[dict[str, Any]] = []

    for input_record in input_records:
        parent_record = input_record.copy()
        savings_plans = parent_record.pop("savingsPlan", [])
        output_records.append(parent_record)

        for savings_plan in savings_plans:
            output_record = parent_record.copy()
            output_record["type"] = "SavingsPlans"
            output_record["unitPrice"] = savings_plan["unitPrice"]
            output_record["retailPrice"] = savings_plan["retailPrice"]
            output_record["reservationTerm"] = savings_plan["term"]
            output_records.append(output_record)

    # pyright: ignore[reportUnknownMemberType]
    output_df = pd.DataFrame.from_records(output_records)
    logger.info("Created %d price items", output_df.shape[0])
    return output_df


def _prepare_fx_prices(prices: pd.DataFrame, currency: str) -> pd.DataFrame:
    required = set(FX_PRICE_IDENTITY) - {"reservationTerm"}
    required.update({"currencyCode", "retailPrice"})
    if prices.empty or not required.issubset(prices.columns):
        raise ValueError(f"Missing price data or identity fields for {currency}")
    if not prices["currencyCode"].eq(currency).all():
        raise ValueError(f"Unexpected price currency when requesting {currency}")

    prices = prices.copy()
    if "reservationTerm" not in prices:
        prices["reservationTerm"] = ""
    else:
        prices["reservationTerm"] = prices["reservationTerm"].fillna("")
    if prices[FX_PRICE_IDENTITY].isna().to_numpy().any():
        raise ValueError(f"Missing price identity values for {currency}")
    if prices.duplicated(FX_PRICE_IDENTITY).any():
        raise ValueError(f"Ambiguous price identities for {currency}")
    prices["retailPrice"] = pd.to_numeric(prices["retailPrice"], errors="raise")
    return prices


def validate_fx_rates(fx_rates: pd.DataFrame, target_currencies: list[str]) -> None:
    """Reject incomplete, duplicate, nonpositive, or nonfinite FX results."""
    if list(fx_rates.columns) != ["currency", "fxRate"]:
        raise ValueError("FX data must have currency and fxRate columns")
    if fx_rates["currency"].duplicated().any() or set(fx_rates["currency"]) != set(
        target_currencies
    ):
        raise ValueError("FX data does not contain exactly the required currencies")
    rates = cast(pd.Series, pd.to_numeric(fx_rates["fxRate"], errors="raise"))
    if not ((rates > 0) & (rates < float("inf"))).all():
        raise ValueError("FX rates must be finite and positive")


def calculate_fx_rates(
    base_currency: str = "USD",
    target_currencies: list[str] | None = None,
    results_filter: str = "",
    max_pages: int = 9999999,
) -> pd.DataFrame:
    """Calculate FX rates by comparing prices across currencies.

    Match the same SKU, region, meter, price type, term, tier, and unit across
    currencies. The first positive, finite matching price pair supplies the rate.
    Missing data, ambiguous identities, and request failures stop the calculation;
    partial results are never returned.

    Args:
        base_currency (str, optional): Base currency for FX rates. Defaults to "USD".
        target_currencies (list[str] | None, optional): List of target currencies to compare.
            If None, uses a default list of common currencies.
        results_filter (str, optional): Filter results string. Defaults to "".
        max_pages (int, optional): Only download max_pages of results. Defaults to 9999999.

    Returns:
        pd.DataFrame: DataFrame with columns: currency, fxRate

    Raises:
        ValueError: Prices cannot be matched safely or a required rate is missing.
        requests.RequestException: A price request fails.
    """
    if target_currencies is None:
        # Default list of common currencies
        target_currencies = ["EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR"]
    if len(target_currencies) != len(set(target_currencies)):
        raise ValueError("Target currencies must be unique")
    if not target_currencies:
        return pd.DataFrame(columns=["currency", "fxRate"])

    logger.info(
        "Calculating FX rates from %s to %s",
        base_currency,
        ", ".join(target_currencies),
    )

    # Get base currency prices
    logger.info("Fetching %s prices...", base_currency)
    base_df = _prepare_fx_prices(
        get_prices(
            currency_code=base_currency,
            results_filter=results_filter,
            max_pages=max_pages,
        ),
        base_currency,
    )

    fx_results: list[dict[str, Any]] = []

    for target_currency in target_currencies:
        logger.info("Fetching %s prices...", target_currency)
        target_df = _prepare_fx_prices(
            get_prices(
                currency_code=target_currency,
                results_filter=results_filter,
                max_pages=max_pages,
            ),
            target_currency,
        )
        merged_df = base_df.merge(
            target_df,
            on=FX_PRICE_IDENTITY,
            suffixes=("_base", "_target"),
            how="inner",
            validate="one_to_one",
        )
        valid_df = merged_df[
            (merged_df["retailPrice_base"] > 0)
            & (merged_df["retailPrice_base"] < float("inf"))
            & (merged_df["retailPrice_target"] > 0)
            & (merged_df["retailPrice_target"] < float("inf"))
        ]
        if valid_df.empty:
            raise ValueError(f"No positive matching prices for {target_currency}")
        first_row = valid_df.iloc[0]
        fx_rate = first_row["retailPrice_target"] / first_row["retailPrice_base"]
        fx_results.append({"currency": target_currency, "fxRate": fx_rate})
        logger.info("Calculated FX rate for %s: %.4f", target_currency, fx_rate)

    fx_df = pd.DataFrame.from_records(fx_results, columns=["currency", "fxRate"])
    validate_fx_rates(fx_df, target_currencies)
    logger.info("Calculated FX rates for %d currencies", len(fx_df))

    return fx_df
