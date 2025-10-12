"""Export Azure Retail Prices for Virtual Machines in USD."""

import api.azureapi as azureapi

# Currency code(s) to use
CURRENCY_LIST = ["USD"]

# Filter
FILTER = "$filter=serviceName eq 'Virtual Machines'"

## Loop through the currencies
for currency_code in CURRENCY_LIST:
    export_df = azureapi.get_prices(currency_code, FILTER)
    # Export to CSV - this is much faster than creating an xlsx file and can just as easily be imported into Excel
    export_file = f"prices_{currency_code}.json"
    print(f"Exporting prices to {export_file}")
    export_df.to_json(export_file, orient="records")
    print(f"Exported prices to {export_file}")
