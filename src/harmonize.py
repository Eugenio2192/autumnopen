from src.harmonization import cost_calculations, cost_harmonization, unit_harmonization
from src.harmonization.unit_transformation_functions import calculate_FCF, HHV_to_LHV
from src.harmonization.cost_transformation_functions import change_currency, index_generator
from src.tools.config_loader import Configuration
import json
config = Configuration.get_instance()
io = config["IO"]
local_config = config["HarmonizationTool"]


def fuel_data_loader():
    with open(io["harmonization_fuels_defalut_path"]) as json_file:
        fuel_data = json.load(json_file)
    return fuel_data

# Uncomment once you have the datasources in the proper directories
#fuel_data = fuel_data_loader()
#idx_map = index_generator()


def mapper(row, fuel_name):
    """
    Nested support function
    """
    fuel_dict = fuel_data[fuel_name]
    LHV = fuel_dict["LHV_GJ"]
    HHV = fuel_dict["HHV_GJ"]
    row["fuel_cost"] = change_currency(fuel_dict["Cost_2019_USD"] / LHV, idx_map, 2019, "USDEUR")
    row["fuel_name"] = fuel_dict["Type"]
    if row["heat_basis"] == "HHV":
        row["heat_rate"] = HHV_to_LHV(row["heat_rate"], HHV, LHV)
        row["heat_rate_cc"] = HHV_to_LHV(row["heat_rate_cc"], HHV, LHV)
    return row


def map_fuel_cost(row, fuel_data, idx_map):
    """
    Maps the fuels of the souzrces into a generalized group of fuels, It is recommended agaisnt this option because
    the heat rates of the reported plants are already consistent with their fuel prices so imposing values causes
    uncertain results
    :param row: row of the dataframe, this methhod only works in a dataframe
    :param fuel_data: Default fuels to override the original values
    :param idx_map: index map for the cost translations
    :return: Updated row
    """
    # Try to extract

    if row["fuel_name"] in local_config["FuelEquivalentNames"]["HardCoals"]:
        row = mapper(row, "Illinois_6_ton")
    elif row["fuel_name"] in local_config["FuelEquivalentNames"]["HardCoals"]:
        row = mapper(row, "powder_river_basin_ton")
    elif row["fuel_name"] in local_config["FuelEquivalentNames"]["Other"]:
        row["fuel_cost"] = 1
        row["fuel_name"] = "powder_river_basin_ton"
    elif row["fuel_name"] == "natural_gas":
        LHV = fuel_data["natural_gas_m3"]["LHV_GJ"]
        HHV = fuel_data["natural_gas_m3"]["HHV_GJ"]
        row["fuel_cost"] = change_currency(fuel_data["natural_gas_m3"]["Cost_2019_USD"] * 1000 / (LHV), idx_map, 2019,
                                           "USDEUR")
        if row["heat_basis"] == "HHV":
            row["heat_rate"] = HHV_to_LHV(row["heat_rate"], HHV, LHV)
            row["heat_rate_cc"] = HHV_to_LHV(row["heat_rate_cc"], HHV, LHV)

    return row


def cost_harmonization_main(input_path, year, same_fuel=False, same_fcf=True, same_capture_eff=True):
    """
    Wrapping function of the Harmonization tool, it converts the values from the input file into the
    harmonized dataframe
    :param input_path: Path of the input dataframe
    :param year: Desired year of conversion, currently does not support 2020
    :param same_fuel: Option to override fuelprices and heatrates from the original studies
    :param same_fcf: Option to override Fixed cost factors from the orignal studies
    :param same_capture_eff: Option to override the capture efficiency from the original studies.
    :return: DataFrame of the updated values, Index map utilized for the production of said dataframe
    """
    df_units = unit_harmonization.match_unit_values(input_path)
    df_costs, idx_map = cost_harmonization.transform_costs(df_units, year)
    # df_costs = df_units
    # idx_map = None
    if same_fuel:
        df_costs = df_costs.apply(lambda row: map_fuel_cost(row, fuel_data, idx_map), axis=1)
    if same_fcf:
        df_costs["FCF"] = calculate_FCF(10, 25)
    if same_capture_eff:
        df_costs["capture_efficiency"] = 0.9
    df_cc = cost_calculations.calc_cc_lcoe_df(df_units)

    return df_cc, idx_map


def harmonization():
    with open(io["harmonization_fuels_defalut_path"], "r") as fuels:
        fuel_data = json.load(fuels)

    df, idx_map = cost_harmonization_main(io["harmonization_input_path"],
                                          local_config["Options"]["CostYear"],
                                          local_config["Options"]["SameFuel"],
                                          local_config["Options"]["SameFCF"],
                                          local_config["Options"]["SameCaptureEfficiency"])

    df.to_csv(io["harmonization_df_output_path"], na_rep="NaN", encoding="iso-8859-1", index=True)
    return


if __name__ == "__main__":
    harmonization()
