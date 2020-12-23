from src.tools.config_loader import Configuration
from src.homogenization.data_operations import DataSource
import pandas as pd
from src.harmonization.unit_transformation_functions import eff_to_hr
config = Configuration.get_instance()
io = config["IO"]
local_config = config["InputHomogenization"]

bio_map = pd.DataFrame({"fuel_type": 3 * ["bioenergy"],
                        "value": ["delta_capex", "delta_om", "delta_heatrate"],
                        "range_low": [80, 0.00055, 1542],
                        "range_high": [325.44, 0.0022, 17052],
                        "reference_value": [325.44, 0.0022, 17052]})


def map_fuel_name(fuel):
    """
    Fixes fuel names
    """
    fuel_match = local_config["CostMatching"]["FuelMatch"]
    return fuel_match[fuel]


def get_reference_value(map, fuel, name):
    """
    Extract reference value from the asssumption map
    :param map: Assumption map
    :param fuel: Fuel of the power plant
    :param name: Name of the cost value
    """
    if name in ["delta_capex", "delta_om"]:
        value = map[(map["fuel_type"] == fuel) & (map["value"] == name)][local_config["CostLevel"]].values[0]
    else:
        value = map[(map["fuel_type"] == fuel) & (map["value"] == name)][local_config["HRLevel"]].values[0]
    return value


def add_assumptions(data):
    """
    Match assumptions with power plants
    :param data: DataFrame with the power plant Data
    :return: DataFrame with updated values
    """
    assumption_map = pd.read_csv(io["harmonization_output_assumption_path"])
    if local_config["IncludeBio"]:
        assumption_map = pd.concat([assumption_map, bio_map])
    for val in assumption_map.value.unique():
        data[val] = data.apply(lambda x: get_reference_value(assumption_map, x.fuel_match, val), axis=1)
    return data


def get_reg_params(map, fuel):
    """
    Helper function to extract regression parameters from the regression map
    :param map: Regression map
    :param fuel: Fuel of the power plant
    """
    idx = map.index[map["Fuel"] == fuel]
    if local_config["HRLevel"] == "range_high":
        slope_corr = map.loc[idx, "slope_err"]
        intersect_corr = map.loc[idx, "intersect_err"]
    elif local_config["HRLevel"] == "range_low":
        slope_corr = -map.loc[idx, "slope_err"]
        intersect_corr = -map.loc[idx, "intersect_err"]
    else:
        slope_corr = 0
        intersect_corr = 0
    slope = map.loc[idx, "slope"] + slope_corr
    intersect = map.loc[idx, "intercept"] + intersect_corr
    return slope, intersect


def calculate_delta_hr(hr, slope, intersect):
    """
    Helper function to calculate delta Heat Rate
    :param hr: Heat rate of the power plant
    :param slope: Slope of the regression
    :param intersect: Intersect of the regression
    :return: Delta Heat Rate
    """
    return slope * hr + intersect


def do_hr_regression(data):
    """
    Apply regression to DataFrame
    :param data: DataFrame with input data
    :return: DataFra,e with the input parameters of the regression
    """
    reg_map = pd.read_csv(io["harmonization_output_regression_path"])
    fuels = ["coal"]
    slopes = {}
    interceptions = {}
    data["heatrate"] = data.predicted_efficiency.apply(eff_to_hr)
    for fuel in fuels:
        slopes[fuel], interceptions[fuel] = get_reg_params(reg_map, fuel)
    data["delta_heatrate"] = data.apply(lambda x: calculate_delta_hr(x.heatrate,
                                                                     slopes[x.fuel_match],
                                                                     interceptions[x.fuel_match]) \
        if x.fuel_match in fuels else x.delta_heatrate, axis=1)
    return data


def match_powerplant_delta_values():
    """
    Wrapper function to match assumptions with power plants
    :return: DataFrame with cost and delta values
    """
    required_columns = ['Country', 'Fueltype', 'Technology', 'Capacity',
                        local_config['RegressionConfig']['X_columns'][2], local_config['RegressionConfig']['X_columns'][3],
                        'predicted_efficiency', 'delta_capex', 'delta_om', 'delta_heatrate', 'heatrate', 'lat', 'lon']
    source = DataSource.from_file(io['processed_pp_input_path'], index_col='id')
    data = source.data
    data['fuel_match'] = data.apply(lambda x: map_fuel_name(x.Fueltype), axis=1)
    data = add_assumptions(data)
    data = do_hr_regression(data)
    data = data[required_columns]
    return data
