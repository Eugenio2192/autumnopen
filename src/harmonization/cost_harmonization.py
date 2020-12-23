"""
Cost index operations, conversion from reference years to an harmonized year
"""
from src.harmonization.cost_transformation_functions import *

# Columns classified for index to be used
capital_cost_columns = ["capital_cost", "lcoe_capex", ]
cc_columns = ["capital_cost_cc", "lcoe_capex_cc", "fixed_om_cc", "variable_om_cc", "lcoe_om_cc"]
om_columns = ["fixed_om", "variable_om", "lcoe_om"]
fuel_columns = ["fuel_cost", "lcoe_fu", "lcoe_fu_cc"]
cost_columns = capital_cost_columns + om_columns + fuel_columns + cc_columns


# Helper functions


def convert_column(row, column, idx_map, new_year, index):
    """
    Generic column conversion function
    :param row: Pandas dataframe row
    :param column: Name of the column to be transformed
    :param idx_map: Index map containing the input and output years
    :param new_year: Goal year of the transformation
    :param index: Index to use for the transformation
    :return: Transformed value as float
    """
    return convert_value(row[column], idx_map, row.basis_year, new_year, index)


def convert_fuels(row, column, idx_map, new_year):
    """
    Performs cost transformation for Fuels
    :param row: Pandas dataframe row
    :param column: Name of to be converted column
    :param idx_map: Index map containing the desired indexes
    :param new_year: Goal year of the transformation
    :return: Converted value
    """
    if row.fuel_type == "coal":
        index = "COALIDX"
    else:
        index = "NGIDX"

    return convert_value(row[column], idx_map, row.basis_year, new_year, index)


def transform_costs(df, new_year=2019):
    """
    Transform cost of the whole dataframe
    :param df: Pandas dataframe containing the data
    :param new_year: Goal year of the transformations
    :return: Transformed dataframe
    """

    df_cost = df.loc[:, cost_columns + ["basis", "fuel_type"]]
    df_cost.loc[:, "basis_year"] = df_cost.loc[:, "basis"].str[:4].astype(int)
    df_cost.loc[:, "currency"] = df_cost.loc[:, "basis"].str[4:7]
    df_cost = df_cost.drop(columns=["basis"])

    years = list(df_cost["basis_year"].unique())
    years.append(new_year)

    idx_map = create_index_map(years)

    # Convert everything into USD for the transformations

    for column in cost_columns:
        df_cost[column] = df_cost.apply(lambda row: change_currency(row[column], idx_map, row["basis_year"], "EURUSD")
        if row.currency == "EUR" else row[column], axis=1)
    df_cost["currency"] = "USD"

    # Convert the values of capital cost using the UCCI

    for column in capital_cost_columns:
        df_cost[column] = df_cost.apply(lambda row: convert_column(row, column, idx_map, new_year, "UCCI"), axis=1)

    for column in om_columns:
        df_cost[column] = df_cost.apply(lambda row: convert_column(row, column, idx_map, new_year, "UOCI"), axis=1)

    for column in cc_columns:
        df_cost[column] = df_cost.apply(lambda row: convert_column(row, column, idx_map, new_year, "CEPCI"), axis=1)

    for column in fuel_columns:
        df_cost[column] = df_cost.apply(lambda row: convert_fuels(row, column, idx_map, new_year), axis=1)

    df_cost["basis_year"] = new_year

    for column in cost_columns:
        df_cost[column] = df_cost.apply(
            lambda row: change_currency(row[column], idx_map, new_year, "USDEUR"), axis=1)
    df_cost["currency"] = "EUR"

    for column in cost_columns:
        df[column] = df_cost[column]
    df["basis"] = "EUR" + str(new_year)

    return df, idx_map
