import pandas as pd
import numpy as np
from scipy.stats import describe, trim_mean, t
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
from matplotlib import rc
import seaborn as sns
import statsmodels.api as sm
from src.tools.config_loader import Configuration

config = Configuration.get_instance()
rc('font', **{'family': 'serif', 'serif': ['Palatino']})
rc('text', usetex=True)
pd.set_option('display.max_columns', None)
io = config["IO"]

columns = ["fuel_type", "value", "range_low", "range_high", "reference_value", "units"]
values = ["delta_capex", "delta_om", "delta_heatrate"]
fuel_types = ["natural_gas", "coal"]


def values_array(df, fuel, value_name, retrofit=True):
    """
    Helper function to extract values from the Input dataframe
    :param df: dataframe, output of CaptureCostHarmonization  tool
    :param fuel: Fuel type of which the values are to be extracted
    :param value_name: name of the column where the desired value is to be extracted from
    :param retrofit: True if the retrofit column is to be considered, False otherwise
    :return: numpy array with the values
    """
    if fuel == "coal":
        if retrofit:
            values = df[(df["fuel_type"] == fuel) & (df["retrofit"])][value_name].dropna().values
        else:
            values = df[df["fuel_type"] == fuel][value_name].dropna().values
    elif fuel == "natural_gas":
        values = df[df["fuel_type"] == fuel][value_name].dropna().values
    else:
        values = np.nan

    return values


def value_stats(values):
    """
    Extract statistics from the values in the Input
    :param values: Numpy array, output of the values_array function
    :param top_per: top precentile to be considered, default is 75
    :param bot_per: lower percentile to be considered, default is 25
    :return: mean of the mix of values, trimmed mean with 50% of the values, standard deviation of the mix, top and bottom percentile values
    """
    stats = describe(values)
    mean = stats.mean
    std = np.sqrt(stats.variance)
    t_stat = t.ppf(1 - 0.025, len(values) - 1)
    dev = t_stat * (std / np.sqrt(len(values)))
    trim_mean_v = trim_mean(values, 0.25)
    upper_val = mean + dev
    lower_val = mean - dev

    return mean, trim_mean_v, std, upper_val, lower_val


def prepare_dataframe(input_path, index_col="label"):
    """
    Prepare the input of the scientific power plant dataset.
    :param input_path: Path of the power plant dataset
    :param index_col: Name of the index column
    :return: DataFrame with delta values
    """
    df = pd.read_csv(input_path, index_col=index_col)
    df = df[df.power_technology != "IGCC"]
    df = df[df.region != "China"]

    df.loc[:, "delta_capex"] = df.loc[:, "capital_cost_cc"] - df.loc[:, "capital_cost"]
    df.loc[:, "delta_lcoe_capex"] = df.loc[:, "lcoe_capex_cc"] - df.loc[:, "lcoe_capex"]
    df.loc[:, "delta_om"] = df.loc[:, "lcoe_om_cc"] - df.loc[:, "lcoe_om"]
    df.loc[:, "delta_heatrate"] = df.loc[:, "heat_rate_cc"] - df.loc[:, "heat_rate"]
    return df


def create_assumption_map(columns, df):
    """
    Use statistical tools to create a map where the assumptions for the different types of technologies
    are mapped
    :param columns: Name of the columns in the assumption map
    :return: DataFrame with assumptions
    """
    assumption_map = pd.DataFrame(columns=columns)

    for fuel in fuel_types:
        for value in values:
            if fuel == "coal" and value == "delta_capex":
                retrofit = True
            else:
                retrofit = False
            array = values_array(df, fuel, value, retrofit=retrofit)
            mean, trim_mean_v, std, top_p, bot_p = value_stats(array)

            if value == "delta_capex":
                units = "2019€_KW"
            elif value == "delta_om":
                units = "2019€_KWh"
            elif value == "delta_heatrate":
                units = "KW_KWh"
            assumption_map = assumption_map.append({"fuel_type": fuel, "value": value, "range_low": bot_p,
                                                    "range_high": top_p, "reference_value": mean, "units": units},
                                                   ignore_index=True)
    return assumption_map


def heat_rate_regression(df, x_cols, y_col):
    """
    Create Heat rate regression model.
    :param df: Scientific data
    :param x_cols: Columns with the x values of the regression
    :param y_col: Objective column of the regression
    :return: regression model
    """
    df = df[~ np.isnan(df[y_col])]
    for col in x_cols:
        df = df[~ np.isnan(df[col])]

    X = df[x_cols].to_numpy()

    y = df[y_col].to_numpy()

    reg = LinearRegression().fit(X, y)
    return reg


def other_regression(df, x_cols, y_col):
    """
    Alternative regression model, this time using statsmodel
    """
    df = df[~ np.isnan(df[y_col])]
    for col in x_cols:
        df = df[~ np.isnan(df[col])]

    X = df[x_cols].to_numpy()
    X = sm.add_constant(X)
    y = df[y_col].to_numpy()
    mod = sm.OLS(y, X)
    res = mod.fit()
    return res
    #print(res.summary())


def create_regression_map(df, only_coal=True):
    """
    Creates a dataframe containing the regression parameters
    :param df: DataFrame with the datapoints the regression is going to be built upon
    :param pnly_coal: Boolean, if true it will only build a regression for coals.
    :return: DataFrame with mapped parameters
    """
    regression_map = pd.DataFrame(columns=["Fuel", "slope", "intercept", "min_val", "max_val"])
    if only_coal:
        df = df[df.fuel_type == "coal"]
    for fuel in df.fuel_type.unique():
        temp_df = df[df["fuel_type"] == fuel].copy()
        regression_hr = heat_rate_regression(temp_df, ["heat_rate"], "delta_heatrate")
        map_dict = {}
        map_dict["Fuel"] = fuel
        map_dict["slope"] = regression_hr.coef_[0]
        map_dict["intercept"] = regression_hr.intercept_
        map_dict["min_val"] = temp_df["heat_rate"].min()
        map_dict["max_val"] = temp_df["heat_rate"].max()
        regression_map = regression_map.append(map_dict, ignore_index=True)
    return regression_map


def _box_plot_deltas(df, ax, value, fuel, label, retrofit=True):
    """
    Plot deltas as boxplots
    """
    if retrofit:
        values = df[(df.retrofit) & (df.fuel_type == fuel)][value].dropna().values
    else:
        values = df[df.fuel_type == fuel][value].dropna().values
    stats = describe(values)

    mean = stats.mean
    std = np.sqrt(stats.variance)
    t_stat = t.ppf(1 - 0.025, len(values) - 1)
    dev = t_stat * (std / np.sqrt(len(values)))
    ax = sns.boxplot(x=values, ax=ax)
    sns.stripplot(x=values, ax=ax, size=4, color=".3", linewidth=0)
    plt.plot([mean, mean], ax.get_ylim(), 'r--')
    plt.plot([mean + dev, mean + dev], ax.get_ylim(), 'r--')
    plt.plot([mean - dev, mean - dev], ax.get_ylim(), 'r--')
    plt.xlabel(label)
    return ax


def _assumptions_to_latex(assumption_map):
    assumption_map = assumption_map.rename(columns={"fuel_type": "Fuel",
                                                    "value": "Value Name",
                                                    "range_low": "Lower Limit",
                                                    "range_high": "Upper Limit",
                                                    "reference_value": "Reference Value",
                                                    "units": "Units"})

    assumption_map["Fuel"] = assumption_map["Fuel"].str.replace("_", " ")
    assumption_map["Value Name"] = assumption_map["Value Name"].str.replace("_", " ")
    assumption_map["Units"] = assumption_map["Units"].str.replace("_", "/")
    print(assumption_map.to_latex(index=False, float_format="%.3f"))


def _regression_to_latex(regression_map):
    print(regression_map.to_latex(index=False))


def _create_plots(df):
    params = [("delta_capex", "natural_gas", "CAPEX from implementing CO2 capture [€/KW]", False),
              ("delta_capex", "coal", "CAPEX from implementing CO2 capture [€/KW]", True),
              ("delta_om", "natural_gas", "Specific OM costs from implementing CO2 capture [€/KWh]", False),
              ("delta_om", "coal", "Specific OM costs from implementing CO2 capture [€/KWh]", False)]
    figs = []

    for i, param in enumerate(params):
        fig, ax = plt.subplots()
        box_plot_deltas(df, ax, *param)
        figs.append(fig)
    plt.show()

def create():
    df = prepare_dataframe(io["harmonization_df_output_path"], index_col="label")
    assumption_map = create_assumption_map(columns, df)
    assumption_map.to_csv(io["harmonization_output_assumption_path"], index = False)


def create():
    """
    Main function to create the assumption maps as csv files.
    """
    df = prepare_dataframe(io["harmonization_df_output_path"], index_col="label")
    assumption_map = create_assumption_map(columns, df)
    assumption_map.to_csv(io["harmonization_output_assumption_path"], index=False)

    # Heat Rate regression Map, Valid only for the Coal
    regression_map = create_regression_map(df)

    res = other_regression(df[df["fuel_type"] == "coal"], ["heat_rate"], "delta_heatrate")
    regression_map["intersect_err"] = res.bse[0]
    regression_map["slope_err"] = res.bse[1]
    print(regression_map)
    regression_map.to_csv(io["harmonization_output_regression_path"], index=False)


if __name__ == "__main__":
    create()
