from src.technoeconomical.cost_operations_functions import *
from src.homogenization.plant_cost_matching import match_powerplant_delta_values
from src.tools.config_loader import Configuration
from src.harmonization.cost_transformation_functions import create_index_map, change_currency
import json
import pandas as pd
config = Configuration.get_instance()
io = config["IO"]
local_config = config["InputHomogenization"]
default_values = local_config["CostOfCCConfig"]["DefaultValues"]

FUELS = local_config["RegressionConfig"]["Fuels"].copy()
if local_config["IncludeBio"]:
    FUELS.append("Bioenergy")
FUEL_DEFAULTS_PATH = io["harmonization_fuels_defalut_path"]


def map_capacity_factor(fuel):
    """
    :param fuel: Select fuel capacity factor
    :return:
    """
    return default_values["CapacityFactor"][fuel]


def calculate_capex_lcoe_dataframe(data):
    """
    Applies CAPEX LCOE calculation at a dataframe level
    :param data: Dataframe with the parameters of the ecuation
    :return: DataFrame with new column contaiing LCOE from CAPEX
    """
    data["capex_lcoe"] = data.apply(lambda x: calc_lcoe_capex(x.delta_capex, default_values["FCF"],
                                                              map_capacity_factor(x.Fueltype)), axis=1)
    return data


def calculate_om_lcoe_dataframe(data):
    """
    Applies Operation and Management LCOE calculation at a dataframe level
    :param data: Dataframe with the parameters of the equation
    :return: DataFrame with new column contaiing LCOE from CAPEX
    """
    data["om_lcoe"] = data.apply(lambda x: calc_lcoe_om(0, x.delta_om, map_capacity_factor(x.Fueltype)), axis=1)
    return data


def load_fuel_defaults(path):
    """
    Load the fuel data
    :param path: Location of the data
    :return: Fuel data in dictionary form
    """
    with open(path, "r") as data:
        fuel_data = json.load(data)
    return fuel_data


def create_fuel_map(fuels):
    """
    Create fuel value map based on the input fuels
    :param fuels: Fuel dictionary
    :return: DataFrame with mapped fuels
    """
    fuel_default_data = load_fuel_defaults(FUEL_DEFAULTS_PATH)
    fuel_name_dict = {fuel_default_data[x]["Type"]: y for x, y in fuel_default_data.items()}
    fuel_map = pd.DataFrame()
    fuel_map["fuel"] = fuels
    currency_map = create_index_map([2019])
    for fuel in fuels:
        key = "_".join(fuel.lower().split(" "))
        idx = fuel_map.index[fuel_map["fuel"] == fuel]
        fuel_map.loc[idx, "emission_factor"] = fuel_name_dict[key]["Emission_Factor_KG_KJ"]
        cost = fuel_name_dict[key]["Cost_2019_USD"] / fuel_name_dict[key]["LHV_GJ"]
        fuel_map.loc[idx, "fuel_cost"] = change_currency(cost, currency_map, 2019, "USDEUR") * local_config["FuelCorrection"]
    fuel_map = fuel_map.set_index("fuel")
    return fuel_map


def calculate_fuel_lcoe_dataframe(data, map):
    """
    Calculate Fuel component of LCOE
    :param data: DataFrame with the input data
    :param map: Fuel map for matching fuel properties
    :return: DataFrame with new column containing Fuel LCOE
    """
    data["fuel_lcoe"] = data.apply(lambda x: calculate_lcoe_fuel(x.delta_heatrate, map.loc[x.Fueltype, "fuel_cost"]),
                                   axis=1)
    return data


def calculate_reference_emissions_dataframe(data, map):
    """
    Calculate captured emissions per energy production unit
    :param data: DataFrame with the input data
    :param map: Map with fuel data
    :return: DataFrame with new column containing reference capture rate
    """
    data["captured_ref"] = data.apply(lambda x: calculate_emissions(x.heatrate + x.delta_heatrate,
                                                                    map.loc[x.Fueltype, "emission_factor"],
                                                                    default_values["CaptureEfficiency"])[1],
                                      axis=1)
    return data


def calculate_yearly_emissions_dataframe(data):
    """
    Calculates yearly emissions
    :param data: DataFrame with the input data
    :return: DataFrame with captured CO2 per Year
    """
    data["capacity_factor_corrected"] = data.apply(lambda x: map_capacity_factor(x.Fueltype), axis=1)
    data["captured"] = data["captured_ref"] * data["Capacity"] * data["capacity_factor_corrected"] * 8760 / 1000000
    return data


def calculate_cost_of_carbon_capture(data):
    """
    Wrapping function
    :return: DataFrame With cost of carbon capture of power plants
    """
    map = create_fuel_map(FUELS)
    data = calculate_capex_lcoe_dataframe(data)
    data = calculate_om_lcoe_dataframe(data)
    data = calculate_fuel_lcoe_dataframe(data, map)
    data = calculate_reference_emissions_dataframe(data, map)
    data = calculate_yearly_emissions_dataframe(data)

    data["lcoe"] = data["capex_lcoe"] + data["om_lcoe"] + data["fuel_lcoe"]
    data["cost_of_cc"] = 1000 * data["lcoe"] / data["captured_ref"]
    return data
