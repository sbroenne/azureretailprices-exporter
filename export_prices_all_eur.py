"""Export Azure Retail Prices in EUR to CSV format."""

import api.azureapi as azureapi

# Currency code(s) to use
CURRENCY_LIST = ["EUR"]

# Loop through the currencies
for currency_code in CURRENCY_LIST:
    export_df = azureapi.get_prices(currency_code)

    # Export to CSV - faster than xlsx and easily imported into Excel
    export_file = f"prices_{currency_code}.csv"
    print(f"Exporting prices to {export_file}")
    export_df.to_csv(export_file, index=False)
    print(f"Exported prices to {export_file}")
