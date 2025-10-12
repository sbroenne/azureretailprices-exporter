"""Export FX Rates calculated from Azure Retail Prices.

This script calculates foreign exchange rates by comparing Azure retail prices
across different currencies. It uses USD as the base currency and calculates
rates for multiple target currencies.

The FX rate calculation uses a specific meterId to ensure consistent comparison
across all currencies, making the calculation more efficient and reliable.
"""

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

# Calculate FX rates using the specific meterId filter
print(f"Calculating FX rates from {BASE_CURRENCY} to multiple currencies...")
print(f"Using meterId filter: {METER_ID}")
fx_df = azureapi.calculate_fx_rates(
    base_currency=BASE_CURRENCY,
    target_currencies=TARGET_CURRENCIES,
    results_filter=f"$filter=meterId eq '{METER_ID}'",
)

# Export to CSV
export_file = "fxrates_usd.csv"
print(f"Exporting FX rates to {export_file}")
fx_df.to_csv(export_file, index=False)
print(f"Exported {len(fx_df)} FX rates to {export_file}")

# Print summary
if len(fx_df) > 0:
    print("\nFX Rate Summary:")
    print(fx_df.to_string(index=False))
