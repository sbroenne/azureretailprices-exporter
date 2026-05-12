"""Export Azure Retail Prices for Virtual Machines HBSv2 Series in USD and EUR."""

import api.azureapi as azureapi

# Currency code(s) to use
CURRENCY_LIST = ["USD", "EUR"]

# Filter
FILTER = "$filter=serviceName eq 'Virtual Machines' and productName eq 'Virtual Machines HBSv2 Series'"

## Loop through the currencies
for currency_code in CURRENCY_LIST:
    export_df = azureapi.get_prices(currency_code, FILTER)
    # Export to CSV - this is much faster than creating an xlsx file and can just as easily be imported into Excel
    export_file = f"prices_{currency_code}.csv"
    print(f"Exporting prices to {export_file}")
    export_df.to_csv(export_file, index=False)
    print(f"Exported prices to {export_file}")
