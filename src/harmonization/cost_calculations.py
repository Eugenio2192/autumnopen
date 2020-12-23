"""
These functtions are used for calculating the LCOE of each one of the rows in an input dataframe
"""
from src.technoeconomical.cost_operations_functions import *
import numpy as np

ref_input_cols = ["capital_cost", "FCF", "fixed_om", "variable_om", "heat_rate"]
cc_input_cols = ["capital_cost_cc", "FCF", "fixed_om_cc", "variable_om_cc", "heat_rate_cc"]

ref_output_cols = ["lcoe_capex", "lcoe_om", "lcoe_fu"]
cc_output_cols = ["lcoe_capex_cc", "lcoe_om_cc", "lcoe_fu_cc"]

general_input_cols = ["fuel_cost", "capacity_factor", "power_net"]


def calculate_lcoe_row(row):
    """
    Support function to calculate LCOE on a Pandas Dataframe
    :param row: This function works only with apply with Pandas
    :return: Modified row
    """
    # reference
    if np.isnan(row["lcoe_capex"]):
        row["lcoe_capex"] = calc_lcoe_capex(row["capital_cost"], row["FCF"], row["capacity_factor"])
    if np.isnan(row["lcoe_om"]):
        if np.isnan(row["fixed_om"]):
            fom = 0
        else:
            fom = row["fixed_om"]
        row["lcoe_om"] = calc_lcoe_om(fom, row["variable_om"], row["capacity_factor"])
    if np.isnan(row["lcoe_fu"]):
        row["lcoe_fu"] = calculate_lcoe_fuel(row["heat_rate"], row["fuel_cost"])

    row["lcoe"] = row["lcoe_fu"] + row["lcoe_om"] + row["lcoe_capex"]

    # cc
    if np.isnan(row["lcoe_capex_cc"]):
        row["lcoe_capex_cc"] = calc_lcoe_capex(row["capital_cost_cc"], row["FCF"], row["capacity_factor"])
    if np.isnan(row["lcoe_om_cc"]):
        if np.isnan(row["fixed_om_cc"]):
            fom = 0
        else:
            fom = row["fixed_om_cc"]
        row["lcoe_om_cc"] = calc_lcoe_om(fom, row["variable_om_cc"], row["capacity_factor"])
    if np.isnan(row["lcoe_fu_cc"]):
        row["lcoe_fu_cc"] = calculate_lcoe_fuel(row["heat_rate_cc"], row["fuel_cost"])

    row["lcoe"] = row["lcoe_fu"] + row["lcoe_om"] + row["lcoe_capex"]
    row["lcoe_cc"] = row["lcoe_fu_cc"] + row["lcoe_om_cc"] + row["lcoe_capex_cc"]
    _, row["captured"] = calculate_emissions(row["heat_rate_cc"], row["fuel_emission_factor"],
                                             row["capture_efficiency"])

    row["cost_of_cc"] = 1000 * (row["lcoe_cc"] - row["lcoe"]) / row["captured"]
    row["cc_capex"] = 1000 * (row["lcoe_capex_cc"] - row["lcoe_capex"]) / row["captured"]
    row["cc_om"] = 1000 * (row["lcoe_om_cc"] - row["lcoe_om"]) / row["captured"]
    row["cc_fu"] = 1000 * (row["lcoe_fu_cc"] - row["lcoe_fu"]) / row["captured"]

    return row


def calc_cc_lcoe_df(df):
    """
    Apply calculate_lcoe_row on dataframe
    :param df: Dataframe in which the LCOE will be calculated
    :return: Modified DataFrame
    """
    df["lcoe"] = 0
    df["lcoe_cc"] = 0
    df["captured"] = 0
    df["cost_of_cc"] = 0
    df["cc_capex"] = 0
    df["cc_om"] = 0
    df["cc_fu"] = 0
    df = df.apply(calculate_lcoe_row, axis=1)
    return df
