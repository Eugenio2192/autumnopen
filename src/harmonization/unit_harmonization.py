from src.harmonization.unit_transformation_functions import *
import pandas as pd
import numpy as np


def custom_labels(df, study_row, tech_row):
    """
    Create labels related to the studies the datapoints are associated
    :param df: dataframe with tabulated Data
    :return:
    """
    labels = []
    for i, row in df.iterrows():
        letters = ["A", "B", "C", "D", "F", "G", "H", "I", "J"]
        j = 0
        label = row[study_row] + "_" + row[tech_row] + "_" + letters[j]
        while label in labels:
            j += 1
            label = row[study_row] + "_" + row[tech_row] + "_" + letters[j]
        labels.append(label)
    return labels


def heat_rate_matching(HR, UNITS, EFF):
    """
    Harmonize Heat rates
    :param HR: Heat rate of the data point, None if it is not availible
    :param UNITS: Units in which the Heat rate is calculated
    :param EFF: Efficiency of the data point if availible
    :return: Unified amount
    """
    if ~ np.isnan(HR):
        amount = hr_dimension_match(HR, UNITS)
    else:
        amount = eff_to_hr(EFF)

    return amount


def match_unit_values(PATH):
    """
    This is the main unit harmonization function, it condenses all the functions in unit transformations.
    :return: Unit harmonized dataframe
    """
    # First step: Import the raw datafile where the sources are represented
    input_df = pd.read_csv(PATH, sep=";", encoding="iso-8859-1", decimal='.', na_values=["NaN"])

    columns = ["label", "region", "p_year", "power_technology", "capture_technology", "fuel_name", "fuel_type",
               "power_gross", "power_net",
               "power_aux", "retrofit", "repower", "capacity_factor", "electric_efficiency", "electric_efficiency_cc",
               "heat_rate",
               "heat_rate_cc", "fuel_emission_factor", "plant_emission", "capture_efficiency", "capital_cost",
               "capital_cost_cc", "FCF",
               "life", "fixed_om", "fixed_om_cc", "variable_om", "variable_om_cc", "fuel_cost", "lcoe_capex",
               "lcoe_om", "lcoe_fu", "lcoe_capex_cc", "lcoe_om_cc", "lcoe_fu_cc", "basis"]
    # Second step: Create empty dataframe with column names
    df = pd.DataFrame(columns=columns)
    # Create custom labels for the different studies, making sure there is no repeated names
    df["label"] = custom_labels(input_df, "Study", "Technology")
    # Match names in the Input Data with the desired output structure
    name_matcher = {"region": "Territory",
                    "power_technology": "Technology",
                    "capture_technology": "CaptureTech",
                    "p_year": "Publication_Year",
                    "fuel_name": "Fuel",
                    "fuel_type": "fuel_general",
                    "power_gross": "P_GROSS",
                    "power_net": "P_NET",
                    "power_aux": "P_AUX",
                    "repower": "Repower",
                    "retrofit": "Retrofit",
                    "capacity_factor": "CF",
                    "electric_efficiency": "ELEC_EFF",
                    "electric_efficiency_cc": "ELEC_EFF_CC",
                    "heat_rate": "HR",
                    "heat_rate_cc": "HR_CC",
                    "fuel_emission_factor": "EF_FUEL",
                    "plant_emission": "EF_PLANT",
                    "capture_efficiency": "CAP_EFF",
                    "capital_cost": "CAPITAL_C_REF",
                    "capital_cost_cc": "CAPITAL_CC",
                    "FCF": "FCF",
                    "life": "LIFE",
                    "fixed_om": "FOM",
                    "fixed_om_cc": "FOM_CC",
                    "variable_om": "VOM",
                    "variable_om_cc": "VOM_CC",
                    "fuel_cost": "FC",
                    "lcoe_capex": "CAP_LCOE",
                    "lcoe_capex_cc": "CAP_LCOE_CC",
                    "heat_basis": "EFF_BASIS",
                    "basis": "BASIS"
                    }
    # Name exceptions where the Data is not going to be copied directly from the source
    exceptions = ["power_net", "heat_rate", "heat_rate_cc", "fuel_emission_factor", "plant_emission",
                  "FCF", "fixed_om", "fixed_om_cc", "fuel_cost"]
    # Run operations
    for name in name_matcher:
        if name not in exceptions:
            df[name] = input_df[name_matcher[name]]

    for name in exceptions:
        if name == "power_net":
            df["power_net"] = input_df.apply(lambda x: x.P_NET if ~np.isnan(x.P_NET) else np.mean([x.P_MAX, x.P_MIN]),
                                             axis=1)
        if name == "heat_rate":
            df["heat_rate"] = input_df.apply(lambda x: heat_rate_matching(x.HR, x.HR_UNITS, x.ELEC_EFF), axis=1)
            df["electric_efficiency"] = df.apply(
                lambda x: x.electric_efficiency if ~np.isnan(x.electric_efficiency) else hr_to_eff(x.heat_rate),
                axis=1)

        if name == "heat_rate_cc":
            df["heat_rate_cc"] = input_df.apply(lambda x: heat_rate_matching(x.HR_CC, x.HR_UNITS, x.ELEC_EFF_CC),
                                                axis=1)
            df["electric_efficiency_cc"] = df.apply(
                lambda x: x.electric_efficiency_cc if ~np.isnan(x.electric_efficiency_cc) else \
                                                    hr_to_eff(x.heat_rate_cc), axis=1)

        if name == "fuel_emission_factor":
            df["fuel_emission_factor"] = input_df.apply(lambda x: fuel_emf_dimension_match(x.EF_FUEL, x.EF_FUEL_UNITS),
                                                        axis=1)

        if name == "plant_emission":
            df["plant_emission"] = input_df.apply(lambda x: plant_emf_dimension_match(x.EF_PLANT, x.EF_PLANT_UNITS),
                                                  axis=1)
            df["fuel_emission_factor"] = df.apply(lambda x: calc_fuel_emf(x.plant_emission, x.heat_rate) \
                                            if np.isnan(x.fuel_emission_factor) else x.fuel_emission_factor, axis=1)

        if name == "FCF":
            df["FCF"] = input_df.apply(lambda x: x.FCF if ~np.isnan(x.FCF) else calculate_FCF(x.DISC_RATE, x.LIFE),
                                       axis=1)
        if name == "fixed_om":
            df["fixed_om"] = input_df.apply(lambda x: fom_harmonization(x.FOM, x.FOM_UNITS, x.P_NET, x.LIFE), axis=1)

        if name == "fixed_om_cc":
            df["fixed_om_cc"] = input_df.apply(lambda x: fom_harmonization(x.FOM_CC, x.FOM_UNITS, x.P_NET, x.LIFE),
                                               axis=1)

        if name == "fuel_cost":
            df["fuel_cost"] = input_df.apply(lambda x: fuel_dimension_match(x.FC, x.FC_UNITS, x.Fuel), axis=1)
    df = df.set_index("label")
    return df
