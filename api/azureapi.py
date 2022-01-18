""" Azure Retail Prices API
"""
import requests_cache
import pandas as pd
from datetime import timedelta
import enlighten


def get_prices(currency_code: str, filter: str = "", max_pages: int = 9999999):
    """ Download prices from the Azure API

    Args:
        currency_code (str): Price currency
        filter (str, optional): Filter results string. Defaults to "". [Examples](https://docs.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices)
        max_pages (int, optional): Only download max_pages of results - only really useful for debugging.  Defaults to 9999999.

    Returns:
        [str]: Name of the exported file
        [pd.DataFrame]: Retails prices as a Pandas Dataframe
        
    """

    # Use requests_cache to temporarily cache results for one day
    # Useful if the script stops unexpectedly and you need to resume
    session = requests_cache.CachedSession('azure_cache', expire_after=timedelta(days=1))

    # Construct the base API url
    api_url = f"https://prices.azure.com/api/retail/prices?currencyCode='{currency_code}'"
    
    # Add optional filter argument
    if len(filter) > 0:
        api_url = f"{api_url}&{filter}"
    
    sku_list =[]

    next_page_link = api_url

    print(f"Starting export for API call: {api_url}")
    page_counter = 0
    
    counter = enlighten.Counter(desc='Exported results:', unit='pages')

    # Loop through the result pages
    while next_page_link is not None and page_counter < max_pages:

        page_counter = page_counter +1

        # Get the next page
        api_request = session.get(next_page_link)
        result_json = api_request.json()

        # Convert the JSON results in a list of dictionaries that can be used by pandas
        for sku_item in result_json["Items"]:
            sku_list.append(sku_item)

        next_page_link = result_json["NextPageLink"]
        counter.update()

    print(f"Completed export of {page_counter} result pages")
    print(f"Loading data into pandas")
    
    # Convert the list into a pandas df
    export_df = pd.DataFrame.from_records(sku_list)

    # Export to CSV - this is much faster than creating an xlsx file and can just as easily be imported into Excel
    export_file = f"prices_{currency_code}.csv"
    print(f"Exporting prices to {export_file}")
    export_df.to_csv(export_file, index=False)
    print(f"Exported prices to {export_file}")

    return export_file, export_df
