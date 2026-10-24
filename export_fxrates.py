"""Export FX Rates calculated from Azure Retail Prices.

This script calculates foreign exchange rates by comparing Azure retail prices
across different currencies. It uses USD as the base currency and calculates
rates for multiple target currencies.

The FX rate calculation uses a specific meterId to ensure consistent comparison
across all currencies, making the calculation more efficient and reliable.
"""

import argparse

import api.azureapi as azureapi

# Base currency (reference currency)
BASE_CURRENCY = "USD"

# Target currencies to calculate FX rates for
# Using common currencies from the Azure Retail Prices API
TARGET_CURRENCIES = [
    "EUR",  # Euro
    "GBP",  # British Pound
    "JPY",  # Japanese Yen
    "CAD",  # Canadian Dollar
    "AUD",  # Australian Dollar
    "CHF",  # Swiss Franc
    "CNY",  # Chinese Yuan
    "INR",  # Indian Rupee
    "BRL",  # Brazilian Real
    "KRW",  # South Korean Won
    "SEK",  # Swedish Krona
    "NOK",  # Norwegian Krone
    "DKK",  # Danish Krone
    "NZD",  # New Zealand Dollar
    "RUB",  # Russian Ruble
    "ZAR",  # South African Rand
]

# MeterId to use for FX rate comparison
# This specific meter is used to ensure consistent price comparison across currencies
METER_ID = "5daea80f-04ac-5385-86f0-b263d23becd2"


def main() -> None:
    """Export all required FX rates, refusing to write incomplete results."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="fxrates_usd.csv")
    args = parser.parse_args()

    fx_df = azureapi.calculate_fx_rates(
        base_currency=BASE_CURRENCY,
        target_currencies=TARGET_CURRENCIES,
        results_filter=f"$filter=meterId eq '{METER_ID}'",
    )
    azureapi.validate_fx_rates(fx_df, TARGET_CURRENCIES)
    fx_df.to_csv(args.output, index=False)


if __name__ == "__main__":
    main()
