import lib.azureapi as azureapi

# Exports Azure Retail Prices in USD - limits to 10 pages. Useful for developing/debugging

# Currency code(s) to use
currency_list = ["USD"]

## Loop through the currencies
for currency_code in currency_list:
    azureapi.get_prices(currency_code, max_pages=10)
    