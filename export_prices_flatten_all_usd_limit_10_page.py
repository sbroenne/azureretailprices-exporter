import api.azureapi as azureapi
import api.flatten as flatten

# Exports Azure Retail Prices in USD and flatten the results - limits to 10 pages. Useful for developing/debugging

# Currency code(s) to use
currency_list = ["USD"]

## Loop through the currencies
for currency_code in currency_list:
    export_file, export_df = azureapi.get_prices(currency_code, max_pages=10)
    flattened_price_list = flatten.flatten_prices(currency_code, export_df)
    