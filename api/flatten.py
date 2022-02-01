""" Flatten retails price list(prices rows -> prices columns)
"""

import pandas as pd
import numpy as nn


def flatten_prices(currency_code: str, export_df: pd.DataFrame):
    """ Flatten retails price list(prices rows -> prices columns)

    Args:
        currency_code (str): Price currency
        export_df (pd.DataFrame): Retails prices as a Pandas Dataframe

    Returns:
        [str]: Name of the exported file
    """

    # Create a flattened version that shows prices in columns instead of rows
    print("Creating flattened version (prices rows -> prices columns)")

    # Add effectiveEndDate column if it doesn't exist
    col_name = "effectiveEndDate"
    if col_name not in export_df:
        export_df[col_name] = nn.NaN

    # Unique product key
    export_df["ProductKey"] = export_df["productName"] + "\\" + export_df[
        "skuName"] + "\\" + export_df["meterName"] + "\\" + export_df[
            "tierMinimumUnits"].astype(str) + "\\" + export_df["armRegionName"]

    # Extract prices
    prices_df = export_df.loc[:, [
        "ProductKey", "retailPrice", "type", "reservationTerm"
    ]]

    # Prices with one row per price

    # Consumption/PAYG
    consumption_df = prices_df.loc[prices_df["type"] == "Consumption"]
    consumption_df = consumption_df.rename(
        columns={"retailPrice": "Consumption"})
    del consumption_df["type"]
    del consumption_df["reservationTerm"]

    # Dev Test
    devtest_df = prices_df.loc[prices_df["type"] == "DevTestConsumption"]
    devtest_df = devtest_df.rename(
        columns={"retailPrice": "DevTestConsumption"})
    del devtest_df["type"]
    del devtest_df["reservationTerm"]

    # Reservations - these contains one row per reservation term (1/3/5 years)
    # Need to be pivoted ot reservationTerm column
    reservations_df = prices_df.loc[prices_df["type"] == "Reservation"]
    del reservations_df["type"]
    reservations_pivot_df = reservations_df.pivot(index="ProductKey",
                                                  columns="reservationTerm",
                                                  values="retailPrice")
    reservations_pivot_df["isReservation"] = True

    # Remove existing pricing columns
    del export_df["type"]
    del export_df["reservationTerm"]
    del export_df["retailPrice"]
    del export_df["unitPrice"]
    del export_df["effectiveStartDate"]

    # Drop duplicates
    export_df = export_df.drop_duplicates("ProductKey")

    # Merge the SKU table with the price tables
    export_df = pd.merge(export_df,
                         consumption_df,
                         how="left",
                         on=["ProductKey", "ProductKey"])
    export_df = pd.merge(export_df,
                         devtest_df,
                         how="left",
                         on=["ProductKey", "ProductKey"])
    export_df = pd.merge(export_df,
                         reservations_pivot_df,
                         how="left",
                         on=["ProductKey", "ProductKey"])

    # Filter out lines where we do not have a Consumption price
    # Only two line items in China who only have DevTestConsumption
    # are affected by this
    # Otherwise, we might get division by zero errors for the savings columns

    export_df = export_df.loc[export_df["Consumption"] > 0]

    # Calculate DevTestConsumption Savings
    col_name = "DevTestConsumption"
    if col_name in export_df:
        export_df[f"{col_name} savings"] = 1 - export_df[col_name] / export_df[
            "Consumption"]
    else:
        # Create the column with empty values
        export_df[col_name] = nn.NaN
        export_df[f"{col_name} savings"] = nn.NaN

    # Calculate hourly prices and savings for reservations

    hours_in_month = 730
    col_name = "1 Year"
    if col_name in export_df:
        export_df[col_name] = export_df[col_name] / 12 / hours_in_month
        export_df[f"{col_name} savings"] = 1 - export_df[col_name] / export_df[
            "Consumption"]
    else:
        # Create the column with empty values
        export_df[col_name] = nn.NaN
        export_df[f"{col_name} savings"] = nn.NaN

    col_name = "3 Years"
    if col_name in export_df:
        export_df[col_name] = export_df[col_name] / 36 / hours_in_month
        export_df[f"{col_name} savings"] = 1 - export_df[col_name] / export_df[
            "Consumption"]
    else:
        # Create the column with empty values
        export_df[col_name] = nn.NaN
        export_df[f"{col_name} savings"] = nn.NaN

    col_name = "5 Years"
    if col_name in export_df:
        export_df[col_name] = export_df[col_name] / 60 / hours_in_month
        export_df[f"{col_name} savings"] = 1 - export_df[col_name] / export_df[
            "Consumption"]
    else:
        # Create the column with empty values
        export_df[col_name] = nn.NaN
        export_df[f"{col_name} savings"] = nn.NaN

    return export_df
