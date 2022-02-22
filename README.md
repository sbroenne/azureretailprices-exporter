# 1. azureretailprices-exporter

Export [Azure Retail Prices](https://docs.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) as **JSON** and convert them to **CSV**.

## 1.1. Functionality

A **thin wrapper** that simply retrieves the results from the REST API, supports _API response pagination_ and converts the results into csv files.

Includes functionality to convert this into a flattened prices list (converting prices rows into prices columns).

It assumes that you are familiar with the actual [Azure API](https://docs.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) (e.g. setting filter parameters).

## 1.2. Prerequisites

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

## 1.3. Usage

Following are some examples how to this script.

### 1.3.1. Export all Azure Products in USD

```console
pipenv run python export_prices_all_usd.py
```

This creates the [Azure Retail Prices Export](prices_USD.csv)-file: prices_USD.csv

### 1.3.2. Export all Azure Products in USD and **flattens** the price list

This makes it much easier to consume the list in Excel and Power BI.

```console
pipenv run python export_prices_flatten_all_usd.py
```

This creates the [flattened version of the export](prices_flattened_USD.csv)-file: prices_flattened_USD.csv

### 1.3.3. Export prices for Virtual Machines HBSv2 Series Virtual Machines in USD and EUR and highlights the usage of API filters

```console
pipenv run python export_prices_with_filter_and_multiple_currencies.py
```

## 1.4. Code Layout

All functionality is encapsulated in [lib/azureapi.py](lib/azureapi.py) and [lib/flatten.py](lib/flatten.py). The **export\_\*.py** scripts are just examples how to use this functionality.

## 1.5. Caching

The script uses [requests_cache](https://pypi.org/project/requests-cache) to temporarily cache API results for one day. This is very useful if the script stops unexpectedly and you need to resume later on.

Cache data is stored in the file [azure_cache.sqlite](azure_cache.sqlite). Deleting this file will clear the cache.

## 1.6. Error Handling

There is none. If you run into issue please check if the actual [Azure API](https://docs.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) works with the filters you have specified.
