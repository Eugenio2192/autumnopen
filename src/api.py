from src.tools.config_loader import Configuration
import pandas as pd
from src.curveproduction.geo_distribution_data import CostDistribution, column_map_pp, column_map_cement, \
    column_map_iron
from src.scenarios.scenario_development import create_index_for_scenario_mapping
from src.harmonize import harmonization
from src.assumptions import create as cost_values
from src.homogenize import create_power_plant_file, create_cost_potential_curve_pp_input
from src.homogenization.cost_of_carbon_capture_iron import create as iron_and_steel
from src.homogenization.cost_of_carbon_capture_cement import create as cement
from src.curveproduction.cost_potential_curve import CostCurve
import warnings
import logging
from matplotlib import rc

rc('text', usetex=False)
config = Configuration.get_instance()
io = config["IO"]

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')


def initialize(industrial=config["InputHomogenization"]["IncludeIndustrial"]):
    """
    Produces the datasets by executing the main steps of data processing framework
    """
    logging.info("Starting harmonization")
    harmonization()
    logging.info("Calculating cost values")
    cost_values()
    logging.info("Creating power plant input file")
    try:
        create_power_plant_file()
    except ValueError:
        msg = "There was an initialization error, please run again"
        logging.error(msg)

    logging.info("Creating power plant cost potential file")
    create_cost_potential_curve_pp_input()
    if industrial:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            logging.info("Creating iron and steel cost potential file")
            iron_and_steel()
            logging.info("Creating cement cost potential file")
            cement()
    return


custom_map = {"id": "index",
              "source": "source",
              "geographical_label": "geographical_label",
              "year": "year",
              "production_capacity": "production_capacity",
              "amount": "amount",
              "cost": "cost",
              "lat": "lat",
              "lon": "lon"}


def column_maps(source):
    """
    Support function to match column name maps with their datasets
    """
    loader_map = {"power_plant": column_map_pp,
                  "cement": column_map_cement,
                  "iron": column_map_iron}
    return loader_map[source]


def loader(source):
    """
    Generic csv loading
    """
    loader_map = {"power_plant": io["cc_pp_output_path"],
                  "cement": io["cement_output_path"],
                  "iron": io["steel_output_path"]}
    return pd.read_csv(loader_map[source])


def matcher(source):
    """
    Matches user input with datasets, the lists can be extended
    """
    matcher_map = {"power_plant": ["coal", "coals", "natural gas", "gas", "bioenergy",
                                   "biomass", "hard coal", "lignite", "Fossil fuels",
                                   "fossil", "basic"],
                   "cement": ["cement"],
                   "iron": ["iron", "steel", "iron and steel"]}

    key = dict(filter(lambda x: source in x[1], matcher_map.items())).keys()

    return list(key)[0]


def create_joined_data(sources):
    """
    Creates a single dataset using the inputs
    :param sources: List of sources, or a single string with the desired source
    :return: DataFrame with the joined values
    """
    if isinstance(sources, str):
        matches = [matcher(sources)]
    elif isinstance(sources, list):
        matches = set([matcher(s) for s in sources])
    else:
        msg = "The sources should be a list of source names or a single name"
        raise TypeError(msg)
    data = {m: loader(m) for m in matches}
    maps = {m: column_maps(m) for m in matches}
    # homogenize
    joined = pd.concat([CostDistribution(data[m], maps[m]).data.reset_index() for m in matches]).drop(columns=["id"])
    joined = joined.reset_index()
    return joined


def assign_points_to_countries(distribution):
    """
    Uses the NUTS data to assign cuntry names to geographical points
    :param distribution: CostDistribution datatype with geographically distribuited points
    :return: New distribution with country labels in the form of ISO codes
    """
    distribution.switch()
    distribution.match_this_nuts_regions(0)
    distribution.switch()
    return distribution


def filter_teritories(df, territories):
    """
    Filters the dataframe for the desired territories
    :param df: Data containing geographical labels
    :param territories: Geographical labels desired
    :return: Filtered DataFrame
    """
    if isinstance(territories, list):
        df = df[df["geographical_label"].isin(territories)]
    else:
        msg = "territories should be a list of country ISO codes"
        raise TypeError(msg)
    return df


def aggregate_nuts(distribution, level):
    """
    Aggregates distributions to the desired NUTS level
    :param distribution: CostDistribution object
    :param level: Desired NUTS level, from 0 to 3
    :return: Aggregated CostDistribution
    """
    distribution.switch()
    distribution.match_this_nuts_regions(level)
    distribution = distribution.aggregate(True)
    distribution.match_this_nuts_regions(0)
    distribution.switch()
    return distribution


def cost_potential_distribution(sources="basic", territories="Europe", agg_nuts_level=-1):
    """
    Wrapper function to generate a cost potential distribution
    :param sources: List or string of distributions
    :param territories: Geographical labels of the desired territories, if "Europe" will take all
    :param agg_nuts_level: NUTS level aggregation, if -1 no aggregation will be perfomed
    :return: CostDistribution with the desired parameters
    """
    # import sources

    joined = create_joined_data(sources)

    distribution = CostDistribution(joined, custom_map)

    # assign point sources to country labels
    distribution = assign_points_to_countries(distribution)

    # filter the points
    if territories != "Europe":
        distribution.data = filter_teritories(distribution.data, territories)

    # aggregate to corresponding NUTS level
    if 4 > agg_nuts_level > -1:
        distribution = aggregate_nuts(distribution, agg_nuts_level)

    return distribution


def scenario_development_one_hot_encoded(sources, scenarios, territory="Europe"):
    """
    Creates a dataframe with the operation of a production facility encoded to its activity in the given
    years
    :param sources: List or string of carbon sources
    :param scenarios: List of Desired scenarios
    :param territory: List of desired territories
    :return: DataFrame with encoded scenarios
    """
    data = cost_potential_distribution(sources, territory, agg_nuts_level=-1)
    data = data.data.reset_index().drop(columns=["id"])
    data.index.rename("id", inplace=True)
    years = [2025, 2030, 2035, 2040, 2045, 2050]
    data["operating_2020"] = True
    for scenario in scenarios:
        for year in years:
            data["{0}_{1}".format(year, scenario)] = False
            index = create_index_for_scenario_mapping(data, year, scenario)
            data.loc[index, "{0}_{1}".format(year, scenario)] = True
    return data


def produce_scenario_curve(df, scenario, year):
    """
    Creates a CostCurve object of the desired scenario and year
    :param df: Dataframe with one hot encoded scenarios
    :param scenario: Desired scenario
    :param year: Desired year
    :return: CostCurve with given parameters
    """
    if year == 2020:
        scend = df[df["operating_2020"]]
    else:
        scend = df[df["{0}_{1}".format(year, scenario)]]
    curve = CostCurve(scend)
    return curve


def produce_scenario_collection(df, scenario, ax):
    """
    Creates a plot containing a collection of Cost Curves for a given scenario
    :param df: One hot encoded scenario DataFrame
    :param scenario: Desired Scenario
    :param ax: Matplotlib axes object
    :returns: Matplotlib ax object
    """
    curve_scen = CostCurve(df)
    curve_scen.plot_sc(ax, 2020)
    for year in [2025, 2030, 2035, 2040, 2045, 2050]:
        curve_scen = produce_scenario_curve(df, scenario, year)
        curve_scen.plot_sc(ax, year)
    return ax


if __name__ == '__main__':
    config.set_value("range_high", "InputHomogenization", "CostLevel")
    initialize()
    Distribution = cost_potential_distribution(["gas", "iron", "cement"], agg_nuts_level=-1)
    Distribution.plot()
