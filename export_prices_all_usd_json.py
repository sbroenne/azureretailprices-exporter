"""Export Azure Retail Prices in USD to JSON format."""

import api.azureapi as azureapi

# Currency code(s) to use
CURRENCY_LIST = ["USD"]

## Loop through the currencies
for currency_code in CURRENCY_LIST:
    export_df = azureapi.get_prices(currency_code)

    # Export to Json
    export_file = f"prices_all_{currency_code}.json"
    print(f"Exporting prices to {export_file}")
    export_df.to_json(export_file, orient="records")
    print(f"Exported prices to {export_file}")
