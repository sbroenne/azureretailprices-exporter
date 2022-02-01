import api.azureapi as azureapi

# Exports Azure Retail Prices for Virtual Machines HBSv2 Series Virtual Machines in USD and EUR

# Currency code(s) to use
currency_list = ["USD"]

# Filter
filter = "$filter=serviceName eq 'Virtual Machines'"

max_pages = 9999

## Loop through the currencies
for currency_code in currency_list:
    export_df = azureapi.get_prices(currency_code, filter, max_pages)
    # Export to CSV - this is much faster than creating an xlsx file and can just as easily be imported into Excel
    export_file = f"prices_{currency_code}.json"
    print(f"Exporting prices to {export_file}")
    export_df.to_json(export_file, orient="records")
    print(f"Exported prices to {export_file}")