import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy import stats
from src.tools.config_loader import Configuration
from matplotlib import rc
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from src.harmonization.unit_transformation_functions import fuel_name_matching, blacks, browns, petcoke

pd.set_option('display.max_columns', None)
config = Configuration.get_instance()
names = config["HarmonizationTool"]["FigureNames"]
io = config["IO"]
rc('font', **{'family': 'serif', 'serif': ['Palatino']})
rc('text', usetex=True)

name_dictionary = {'region': 'Region', 'p_year': "Publication Year", 'power_technology': 'Power Technology',
                   'capture_technology': "Capture Technology",
                   'fuel_name': "Fuel Name", 'fuel_type': "Fuel Type", 'power_gross': "Gross Power",
                   'power_net': "Net Power", 'power_aux': "Aux Power", 'retrofit': "Retrofit",
                   'repower': "Repower", 'capacity_factor': "Capacity Factor",
                   'electric_efficiency': "Electric Efficiency", 'electric_efficiency_cc': "Electric Efficiency CC",
                   'heat_rate': "Heat Rate", 'heat_rate_cc': "Heat Rate CC", 'fuel_emission_factor': "Fuel Emission F.",
                   'plant_emission': "Plant Emissions", 'capture_efficiency': "Capture Efficiency",
                   'capital_cost': "Capital Cost", 'capital_cost_cc': "Capital Cost CC", 'life': "Life",
                   'fixed_om': "Fixed OM", 'fixed_om_cc': r"Fixed OM CC", 'variable_om': "Variable OM",
                   'variable_om_cc': r"Variable OM CC", 'fuel_cost': "Fuel Cost",
                   'lcoe_capex': r"LCOE CAPEX",
                   'lcoe_om': r"LCOE OM", 'lcoe_fu': r"LCOE Fuel",
                   'lcoe_capex_cc': r"LCOE CAPEX CC",
                   'lcoe_om_cc': r"LCOE OM CC", 'lcoe_fu_cc': r"LCOE Fuel CC",
                   'basis': "Basis", 'heat_basis': "Heat Value Basis", 'lcoe': "LCOE",
                   'lcoe_cc': r"LCOE CC", 'captured': "Captured",
                   'cost_of_cc': "Cost of carbon capture", 'cc_capex': "CAPEX component",
                   'cc_om': r"OM component", 'cc_fu': "Fuel component"}


def r2(x, y):
    return stats.pearsonr(x, y)[0] ** 2


def change_width(ax, new_value):
    for patch in ax.patches:
        current_width = patch.get_width()
        diff = current_width - new_value

        # we change the bar width
        patch.set_width(new_value)

        # we recenter the bar
        patch.set_x(patch.get_x() + diff * .5)


def min_max_norm(series):
    min_v = series.min()
    max_v = series.max()
    normal = (series - min_v) / (max_v - min_v)
    return normal


def prepare_df_for_plotting():
    df = pd.read_csv(io["harmonization_df_output_path"], index_col="label")
    df = df.rename(columns=name_dictionary)
    df = df.drop(columns=["FCF", 'Capture Efficiency'])
    df = df.reset_index()
    df.label = df.label.str.replace("_", " ")
    df["Fuel Name"] = df.apply(lambda x: fuel_name_matching(x["Fuel Name"], blacks, browns, petcoke), axis=1)
    df = df[df["Power Technology"] != "IGCC"]
    df = df[df["Fuel Name"] != "Petcoke"]
    df["Power Technology"] = df["Power Technology"].replace("UCPC", "SCPC")
    df["Power Technology"] = df["Power Technology"].replace("CFB", "SUBC")
    return df


def create_correlation_matrix(df):
    fig, ax = plt.subplots(figsize=(22, 10))
    matrix = abs(df.corr())
    ax = sns.heatmap(matrix, annot=True, cmap="RdYlBu_r")
    # ax.set_title("Absolute correlation matrix of the Cost of Carbon Capture variables")

    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()
    # fig.subplots_adjust( bottom=0.17, left = 0.09 )
    return fig, ax


def create_bar_plots(df):
    with plt.style.context('seaborn-darkgrid'):
        fig, ax = plt.subplots(figsize=(10.8, 15.2))
        df_cost_composition = df[df["Power Technology"] != "IGCC"][
            ["label", "Power Technology", "CAPEX component", "OM component", "Fuel component",
             "Cost of carbon capture"]]
        df_cost_composition["sorting_num"] = df_cost_composition.apply(
            lambda x: 1 if x["Power Technology"] == "NGCC" else 0,
            axis=1)
        df_cost_composition = df_cost_composition.sort_values(["sorting_num", "Cost of carbon capture"])
        df_cost_composition = df_cost_composition.set_index("label")
        df_cost_composition.iloc[:, :-2].plot.barh(stacked=True, ax=ax, cmap="RdYlBu")
        # ax.set_xticklabels( df_cost_composition["label"].to_list() )
        ax.legend(["Capex", "OM", "Fuel"])
        ax.set_xlabel("Cost of Carbon capture [€ / tC$O_2$]", fontsize=20)
        ax.set_ylabel("")
        ax.tick_params(axis='both', which='major', labelsize=15)
        fig.tight_layout()
    return fig, ax


def scatter_plant_type(df):
    with plt.style.context('seaborn-darkgrid'):
        fig, ax = plt.subplots(figsize=(12, 10))
        sns.scatterplot(x="Power Technology", y="Cost of carbon capture", hue="Retrofit", data=df, palette="RdBu_r",
                        s=200,
                        alpha=1)
        ax.set_xlabel("Power Technology", fontsize=20)
        ax.set_ylabel("Cost of Carbon Capture", fontsize=20)
        ax.tick_params(axis='both', which='major', labelsize=15)
        fig.tight_layout()
        return fig, ax


def scatter_fuel_type(df):
    with plt.style.context('seaborn-darkgrid'):
        fig, ax = plt.subplots(figsize=(12, 10))
        sns.scatterplot(x="Fuel Name", y="Cost of carbon capture", hue="Retrofit", data=df, palette="RdBu_r", s=200,
                        alpha=1)
        ax.set_xlabel("Power Technology", fontsize=20)
        ax.set_ylabel("Cost of Carbon Capture", fontsize=20)
        ax.tick_params(axis='both', which='major', labelsize=15)
        fig.tight_layout()
        return fig, ax


def scatter_capacity_vs_cost(df):
    fig, ax = plt.subplots(figsize=(12, 10))
    sns.scatterplot(x="Net Power", y="Cost of carbon capture", hue="Power Technology", data=df, s=200, alpha=0.5, ax=ax)
    return fig, ax


def plot_regressions(df, x_column, y_column, plot_column, x_units, y_units):
    if len(df[plot_column].unique()) == 3:

        fig = plt.figure(figsize=(22, 16))
        axesf = []
        gs = gridspec.GridSpec(2, 4)
        gs.update(wspace=0.5)
        axesf.append(fig.add_subplot(gs[0, :2], ))
        axesf.append(fig.add_subplot(gs[0, 2:]))
        axesf.append(fig.add_subplot(gs[1, 1:3]))
    else:
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axesf = axes.flat
    for i, value in enumerate(df[plot_column].unique()):
        data = df[(df[plot_column] == value) & (~np.isnan(df[x_column]))]
        sns.regplot(x=x_column, y=y_column, data=data, ax=axesf[i], color="Black")
        axesf[i].set_title(value)
        axesf[i].set_ylabel(y_column + "[" + y_units + "]")
        axesf[i].set_xlabel(x_column + "[" + x_units + "]")
        try:
            axesf[i].text(1, 1, "R2= {:04.3f}".format(r2(data[x_column], data[y_column])), ha="right", va="bottom",
                          size=8, color='black', transform=axesf[i].transAxes)
        except ValueError:
            pass
        fig.tight_layout()
    return fig, axesf


def multiple_boxplots(df, x_column, y_column, plot_column, y_units):
    if len(df[plot_column].unique()) == 3:

        fig = plt.figure(figsize=(22, 16))
        axesf = []
        gs = gridspec.GridSpec(2, 4)
        gs.update(wspace=0.5)
        axesf.append(fig.add_subplot(gs[0, :2], ))
        axesf.append(fig.add_subplot(gs[0, 2:]))
        axesf.append(fig.add_subplot(gs[1, 1:3]))
    else:
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        axesf = axes.flat
    for i, value in enumerate(df[plot_column].unique()):
        data = df[df[plot_column] == value]
        sns.boxplot(x=x_column, y=y_column, data=data, ax=axesf[i])

        sns.stripplot(x=x_column, y=y_column, data=data, size=4, color=".3", linewidth=0, ax=axesf[i])
        axesf[i].set_title(value)
        axesf[i].set_ylabel(y_column + " [" + y_units + "]")
        axesf[i].set_xlabel(x_column)
        fig.tight_layout()
    return fig, axesf


def boxplot_fuels(df, x_col, y_col):
    fig, ax = plt.subplots(figsize=(4.8, 4.8))

    legend_elements = [Line2D([0], [0], marker='o', color='w', label='Naims Coal Reference Value',
                              markerfacecolor='indianred', markersize=10),
                       Line2D([0], [0], marker='o', color='w', label='Naims Natural Gas Reference Value',
                              markerfacecolor='cornflowerblue', markersize=10)]

    sns.boxplot(x=x_col, y=y_col, data=df, ax=ax, boxprops=dict(alpha=.3))

    sns.stripplot(x=x_col, y=y_col, data=df,
                  size=4, color=".3", linewidth=0, ax=ax)
    ax.plot(0.0, 35.85, marker="o", color="indianred")
    ax.plot(1.0, 35.85, marker="o", color="indianred")
    ax.plot(2.0, 66.44, marker="o", color="cornflowerblue")
    ax.legend(handles=legend_elements, loc='upper left')
    ax.set_ylabel("Cost of Carbon Capture [2019€/tonCO2]")
    ax.set_xlabel("General Fuel Classification")
    return fig, ax
