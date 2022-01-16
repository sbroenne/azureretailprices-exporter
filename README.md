# azureretailprices-exporter

Export [Azure Retail Prices](https://docs.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) as **JSON** and saves them as **CSV**.

## Functionality

A **thin wrapper** that simply retrieves the results from the REST API, supports *API response pagination* and converts the results into csv files.

It assumes that you are familiar with the actual [Azure API](https://docs.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) (e.g. setting filter parameters).

## Usage

The script requires the following pre-requisites to be installed:

- [pandas](https://pandas.pydata.org/) (CSV export)
- [requests_cache](https://pypi.org/project/requests-cache/) (caching requests to the API for a limited amount of time)
- [enlighten](https://pypi.org/project/enlighten/) (status bar)

Either install them via **pip** or preferably use a virtual environment (**Pipenv**). I have only tested the code on Python 3.9.

In case you use **Pipenv**:

Install the pre-requisites.

```console
pipenv install
```

**Example:** This will export all Azure Products in USD.

```console
pipenv run python export_prices_all_usd.py
```

**Example:** This exports prices for Virtual Machines HBSv2 Series Virtual Machines in USD and EUR and highlights the usage of API filters.

```console
pipenv run python export_prices_with_filter_and_multiple_currencies.py
```

## Code Layout

API functionality is encapsulated in [azureapi.py](azureapi.py). The **export_*.py** scripts are just examples how to use this functionality.

## Caching

The script uses [requests_cache](https://pypi.org/project/requests-cache) to temporarily cache API results for one day. This is very useful if the script stops unexpectedly and you need to resume later on.

Cache data is stored in the file [azure_cache.sqlite](azure_cache.sqlite). Deleting this file will clear the cache.

## Error Handling

There is none. If you run into issue please check if the actual [Azure API](https://docs.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) works with the filters you have specified.
