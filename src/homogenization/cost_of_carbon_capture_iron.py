from src.tools.config_loader import Configuration
from src.harmonization.cost_transformation_functions import convert_value, index_generator
import pandas as pd
config = Configuration.get_instance()
pd.set_option('display.max_columns', None)
io = config["IO"]
#idx_map = index_generator()
# Data from Kuramochi et al. 2012

SPECIFIC_CAPTURE_BF = 0.89  # t / tpig iron
SPECIFIC_CAPTURE_COREX = 2.5
SPECIFIC_CAPTURE = SPECIFIC_CAPTURE_BF if config["InputHomogenization"]["SteelMethod"] == "BF" else SPECIFIC_CAPTURE_COREX
PIG_TO_STEEL = 0.997 / 0.95

PIG_TO_IRON = 0.98 / 0.95
#uncomment when you have the data
#SPECIFIC_COST_BF = convert_value(420, idx_map, 2007, 2019, "CEPCI")  # t / 2007€ / troll
#SPECIFIC_COST_COREX = convert_value(400, idx_map, 2007, 2019, "CEPCI")
#SPECIFIC_COST_REF = convert_value(400, idx_map, 2007, 2019, "CEPCI")
#SPECIFIC_COST = SPECIFIC_COST_BF if config["InputHomogenization"]["SteelMethod"] == "BF" else SPECIFIC_COST_COREX
SCALING_FACTOR = -0.2
REFERENCE_SCALE = 4  # Mt/y


def calculate_specific_captured_carbon_steel(production, specific_capture):
    """
    Calculate the specific captured carbon per production unit
    :param production: Production per year
    :param specific_capture: Capture related to the specified production
    :return: Amount of captured carbon
    """
    return production * specific_capture * 1000


def calculate_specific_cost(production, specific_cost, reference_cost):
    """
    Calculate the cost per production unit
    :param production: The specific production of the steel plant, per year
    :param specific_cost: The cost per production unit of the capture plant
    :param reference_cost: The cost per production unit the reference plant
    :return: cost per production unit
    """
    scaled_ref = ((production / REFERENCE_SCALE) ** SCALING_FACTOR) * reference_cost
    scaled_cost = ((production / REFERENCE_SCALE) ** SCALING_FACTOR) * specific_cost
    return production * (scaled_cost - scaled_ref) * 1000


def calculate_cost_of_carbon_capture_steel(specific_cost, specific_captured_amount):
    """
    Calculate the ocost per ton of CO2 captured
    :param specific_cost: The specific cost of capture, money per year
    :param specific_captured_amount: The specific captured amount per year
    :return: Cost per ton CO2
    """
    return specific_cost / specific_captured_amount


def cost_of_carbon_capture_steel():
    """
    Unifying function
    """
    df = pd.read_csv(io["IRON_INPUT_PATH"], **config["InputConfig"]["iron"])
    data = df["CapacityM"].values
    amounts = [calculate_specific_captured_carbon_steel(val, SPECIFIC_CAPTURE) for val in data]  # tco2/year
    costs_s = [calculate_specific_cost(val, SPECIFIC_COST, SPECIFIC_COST_REF) for val in data]  # €2019/ y
    costs = [calculate_cost_of_carbon_capture_steel(c, a) for c, a in zip(costs_s, amounts)]
    amountsmt = [am / 1000 for am in amounts]
    df_out = df.copy()
    df_out["AmountCapturedMtY"] = amountsmt
    df_out["CostOfCarbonCaptureEURtonCO2"] = costs
    df_out["Source"] = "IronSteel"
    df_out["Year"] = 2019
    return df_out


def create():
    df = cost_of_carbon_capture_steel()
    df.to_csv(io["steel_output_path"], index=True)


if __name__ == "__main__":
    create()
