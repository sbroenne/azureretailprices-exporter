import azureapi

# Exports Azure Retail Prices in USD

# Currency code(s) to use
currency_list = ["USD"]

## Loop through the currencies
for currency_code in currency_list:
    export_file = azureapi.get_prices(currency_code)
    