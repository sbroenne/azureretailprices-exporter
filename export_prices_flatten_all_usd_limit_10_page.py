import api.azureapi as azureapi
import api.flatten as flatten

# Exports Azure Retail Prices in USD and flatten the results - limits to 10 pages. Useful for developing/debugging

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

    flattened_price_list = flatten.flatten_prices(currency_code, export_df)
    # Export flattened file
    export_file = f"prices_flattened_{currency_code}.csv"
    print(f"Exporting prices to {export_file}")
    export_df.to_csv(export_file, index=False)
    print(f"Exported flattened prices to {export_file}")
