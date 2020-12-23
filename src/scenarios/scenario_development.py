import pandas as pd
from src.tools.config_loader import Configuration
from operator import or_ as union
from functools import reduce
import numpy as np

config = Configuration.get_instance()
io = config["IO"]
local_config = config["CostCurveConfig"]

column_map = {"id": "id",
              "source": "source",
              "geographical_label": "geographical_label",
              "year": "year",
              "production_capacity": "production_capacity",
              "amount": "amount",
              "cost": "cost",
              "lat": "lat",
              "lon": "lon"}


def create_scenario_dataframes_geco(scenario):
    """
    Reads GECO dataset and creates a dataframe of the given scenario
    """
    df_sc = pd.read_csv(io["scenario_geco_path"])
    df_sc_europe = df_sc.loc[df_sc["Country"] == "EU28"]
    df_scenario = df_sc_europe.loc[df_sc_europe["Scenario"] == scenario]

    return df_scenario


def unique_scenarios():
    """
    Find unique scenarios in the GECO dataset
    """
    return pd.read_csv(io["scenario_geco_path"]).Scenario.unique()


def fetch_objective_value(df, fuel, year):
    """
    Get specific energy production for the desired fuel in the given year
    """
    if fuel in ["Natural Gas", "natural gas"]:
        fuel = "Gas"
    if fuel == "Fossil fuels":
        return df.loc[(df.Level1 == "Fossil fuels") & (df.Year == year)].Value.sum()
    elif fuel in ["Gas", "Coal", "Biomass"]:
        return df.loc[(df.Level2 == fuel) & (df.Year == year)].Value.values[0]


def close_powerplants(df, objective, capacity_factor, fuel, year):
    """
    Simple algorithm to close power plants based on a given objetive value
    """
    df = df.copy()
    power = objective * 1000 / (capacity_factor * 8.6)
    if fuel == "Coal" and year >= 2038:
        drop_index = df.loc[(df["geographical_label"] == "DE") & (df["source"].isin(["Hard Coal", "Lignite"]))].index
        df = df.drop(drop_index)

    while df.production_capacity.sum() > power:
        min_year = df.year.min()
        drop_index_year = df.loc[(df["year"] == min_year)].index
        df_year = df.loc[drop_index_year]
        min_prod = df_year.production_capacity.min()
        drop_index = df_year.loc[(df_year["production_capacity"] == min_prod)].index
        df = df.drop(drop_index)
    return df.index


def map_capacity_factor(fuel):
    """
    Get capacity factor of the plant from the config file
    """
    return local_config["Scenario"]["CapacityFactors"][fuel]


def close_power_plants_per_fuel(df, fuel, year, scenario_df):
    """
    Apply the close power plants algorithm per fuel
    """
    if fuel == "Coal":
        df_cut = df.loc[df.source.isin(["Hard Coal", "Lignite"])].copy()
    else:
        df_cut = df.loc[df.source == fuel].copy()
    if fuel in ["Lignite", "Hard Coal", "Coal", "Coals"]:
        fuel_s = "Coal"
    elif fuel in ["Bioenergy"]:
        fuel_s = "Biomass"
    elif fuel in ["Natural Gas"]:
        fuel_s = "Gas"
    capacity_factor = map_capacity_factor(fuel_s)
    objective = fetch_objective_value(scenario_df, fuel_s, year)
    index = close_powerplants(df_cut, objective, capacity_factor, fuel, year)
    return index


def idx_union(mylist):
    """
    Support funcion to create an index
    """
    idx = reduce(union, (index for index in mylist))
    return idx


def create_scenario_data_by_points(data, year, scenario):
    """
    Creates a scenario dataset at point resolution
    """
    final_index = create_index_for_scenario_mapping(data, year, scenario)
    return data.loc[final_index]


def query_scenario_data(scenario):
    """
    Get the desired scenario
    """
    scenario_data = create_scenario_dataframes_geco(scenario)
    return scenario_data


def create_index_for_scenario_mapping(data, year, scenario):
    """
    Creates an updated index to create a scenario dataset
    """
    scendata = query_scenario_data(scenario)
    idx_dic = {"others": data[~(data["source"].isin(["Lignite", "Hard Coal", "Natural Gas", "Bioenergy"]))].index}
    for fuel in ["Coal", "Natural Gas", "Bioenergy"]:
        idx_dic[fuel] = close_power_plants_per_fuel(data, fuel, year, scendata)
    idx_list = list(idx_dic.values())
    final_index = idx_union(idx_list)
    return final_index


def create_scenario_data_by_clusters(data, year, scenario, step=50):
    """
    Creates scenarios using clustered points
    """
    data = data.copy()
    data["amount"] = data["amount"] / data["production_capacity"]
    scendata = create_scenario_dataframes_geco(scenario)
    for fuel in ["Coal", "Natural Gas", "Bioenergy"]:
        if fuel in ["Lignite", "Hard Coal", "Coal", "Coals"]:
            fuel_s = "Coal"
            values = data.loc[data.source.isin(["Lignite", "Hard Coal"]), "production_capacity"]
        elif fuel in ["Bioenergy"]:
            fuel_s = "Biomass"
            values = data.loc[data.source == fuel, "production_capacity"]
        elif fuel in ["Natural Gas"]:
            fuel_s = "Gas"
            values = data.loc[data.source == fuel, "production_capacity"]
        objective = fetch_objective_value(scendata, fuel_s, year)
        capacity_factor = map_capacity_factor(fuel_s)
        new_series = calculate_production_change(values, objective, capacity_factor, step=step)

        data.update(new_series)
    data["amount"] = data["amount"] * data["production_capacity"]
    return data


def calculate_production_change(values, objective, capacity_factor, step=50):
    """
    Porcentual changes of production for the cluster scenario production
    """
    new_vals = values.values
    index = values.index
    power = objective * 1000 / (capacity_factor * 8.6)
    total_sum = np.sum(new_vals)
    i = 0
    s = new_vals.shape[0]
    if power > total_sum:
        def test(x, y):
            return x > y
    else:
        def test(x, y):
            return x < y
        step = -step
    while test(power, total_sum):
        new_vals[i % s] = max(new_vals[i % s] + step, 0)
        total_sum = np.sum(new_vals)
        i += 1
    return pd.Series(data=new_vals, name="production_capacity", index=index)
