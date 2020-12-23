from src.homogenization.proxy_efficiency import ppm_proxy_efficiency
from src.homogenization.data_operations import DataSource
from src.tools.config_loader import Configuration
from src.homogenization.plant_cost_matching import match_powerplant_delta_values
from src.homogenization.cost_of_carbon_capture_powerplants import calculate_cost_of_carbon_capture
config = Configuration.get_instance()
io = config["IO"]
local_config = config["InputHomogenization"]


def create_power_plant_file():
    """
    Contains all the procedures to create the power plant input file based on the power plant matching data
    """
    required_columns = ["id", "Country", "Fueltype", "Technology", "Capacity",
                        local_config["RegressionConfig"]["X_columns"][2], local_config["RegressionConfig"]["X_columns"][3],
                        "predicted_efficiency", "lat", "lon"]
    data = ppm_proxy_efficiency(mode=local_config["RegressionConfig"]["Mode"], include_bio=local_config["IncludeBio"])
    data = data[data.Operating != "shutdown"]
    data = data[required_columns]
    commissionCol = local_config["RegressionConfig"]["X_columns"][2]
    if local_config["FillYear"] == "mean":
        data.loc[:, commissionCol] = data.loc[:, commissionCol].fillna(int(data.loc[:, commissionCol].mean()))
    elif type(local_config["FillYear"]) == int:
        data.loc[:, commissionCol] = local_config["FillYear"]
    data = data.set_index("id")
    power_plant_input = DataSource(data=data, local_path=io["processed_pp_input_path"])
    power_plant_input.export_data(io["processed_pp_input_path"])


def create_cost_potential_curve_pp_input():
    """
    Calculates the cost of carbon capture and outputs a dataframe with the data requiered to produce the
    cost potential distributions and curves.
    """
    required_columns = ["Country", "Fueltype", "Technology", "Capacity", local_config["RegressionConfig"]["X_columns"][2],
                        "predicted_efficiency", "captured", "cost_of_cc", "lat", "lon"]
    rename_map = {"Fueltype": "Fuel",
                  "predicted_efficiency": "Efficiency",
                  "Capacity": "CapacityMW",
                  "captured": "AmountCapturedMtY",
                  "cost_of_cc": "CostOfCarbonCaptureEURtonCO2"}
    data = match_powerplant_delta_values()

    data = calculate_cost_of_carbon_capture(data)
    data = data[required_columns]
    data = data.rename(columns=rename_map)
    power_plant_input = DataSource(data=data, local_path=io["cc_pp_output_path"])
    power_plant_input.export_data(io["cc_pp_output_path"])


if __name__ == "__main__":
    create_power_plant_file()
    create_cost_potential_curve_pp_input()
