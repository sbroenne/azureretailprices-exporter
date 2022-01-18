import api.azureapi as azureapi
import api.flatten as flatten

# Exports Azure Retail Prices for Virtual Machines HBSv2 Series Virtual Machines in USD and EUR -  and flatten the results

# Currency code(s) to use
currency_list = ["USD", "EUR"]

# Filter
filter="$filter=serviceName eq 'Virtual Machines' and productName eq 'Virtual Machines HBSv2 Series'"

## Loop through the currencies
for currency_code in currency_list:
    export_file, export_df = azureapi.get_prices(currency_code, filter)
    flattened_price_list = flatten.flatten_prices(currency_code, export_df)
   