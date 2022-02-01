import api.azureapi as azureapi

# Exports Azure Retail Prices in USD

# Currency code(s) to use
currency_list = ["USD"]
# Filter
filter = "$filter=serviceName eq 'Virtual Machines'"

## Loop through the currencies
for currency_code in currency_list:
    export_df = azureapi.get_prices(currency_code, filter, max_pages=10)

    # Export to Json
    export_file = f"prices_{currency_code}.json"
    print(f"Exporting prices to {export_file}")
    export_df.to_json(export_file, orient="records")
    print(f"Exported prices to {export_file}")
