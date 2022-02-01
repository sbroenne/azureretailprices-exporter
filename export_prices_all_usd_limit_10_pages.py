import api.azureapi as azureapi

# Exports Azure Retail Prices in USD - limits to 10 pages. Useful for developing/debugging

# Currency code(s) to use
currency_list = ["USD"]

## Loop through the currencies
for currency_code in currency_list:
    export_df = azureapi.get_prices(currency_code, max_pages=10)

    # Export to CSV - this is much faster than creating an xlsx file and can just as easily be imported into Excel
    export_file = f"prices_{currency_code}.csv"
    print(f"Exporting prices to {export_file}")
    export_df.to_csv(export_file, index=False)
    print(f"Exported prices to {export_file}")
