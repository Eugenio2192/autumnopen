import pandas as pd
import locale
import matplotlib.pyplot as plt
from matplotlib import rc
from src.tools.config_loader import Configuration
rc('font',**{'family':'serif','serif':['Palatino']})
rc('text', usetex=False)
config = Configuration.get_instance()
locale.setlocale(locale.LC_NUMERIC, '')
import numpy as np

# Paths
io = config["IO"]
input_config = config["InputConfig"]
# Figure output
fig_path =io["figures_path"] / "index_development_wiki_example.png"
# Test year values, the tool does not work currently with 2020 Data.

years = [2000,
2002,
2005,
2007,
2008,
2010,
2011,
2012,
2013,
2014,
2019,
]

# Index Data sources configurations, here the path represents the location of hte file in the repository,
# the value_column is the name of the column of the index in the databasae, year_column/date_column is the name of the
# column where the temporal Data is stored
# Basic indexes go through a general extraction script, aggregated indexes are reported in daily or monthly basiss so
# they are aggregated per year
# Rolled indexes are also aggregated but in a rolling average basis
basic_indexes = {
    "UOCI" : {"path" : io["ihs_path"], **input_config["index"]["uoci"]},
    "UCCI" : {"path" : io["ihs_path"], **input_config["index"]["ucci"]},
    "CEPCI": {"path": io["cepci_path"], **input_config["index"]["cepci"]},
    "COALIDX" : {"path" : io["coalidx_path"], **input_config["index"]["coalidx"]}
           }
aggregated_indexes = {"EURUSD" : {"path" : io["eurusd_path"], **input_config["index"]["eurusd"]},
                      "NGIDX" : {"path" : io["ngidx_path"],**input_config["index"]["ngidx"]}
                      }

rolled_indexes = {}

# rolled_indexes = {"COALIDX" : {"path" : coal_path,
#                      "value_column" : "Nominal",
#                      "date_column" : "Year",
#                      "sep" : ";"},
#                   "NGIDX" : {"path" : ng_path,
#                      "value_column" : "Rate",
#                      "date_column" : "Date",
#                      "sep" : ";",
#                      "decimal" : ","}}

# These functions are helper functions for the process of extracting indexes

def basic_values(years, path, value_column, year_column, **kwargs):
    """
    This is the basic extraction function, it opens the file and gets a list of values that are associated to the years
    in the Input list, this works with pandas dataframes
    :param years: List of years to be extracted
    :param path: Path of the Data source
    :param value_column: Name of the column where the value to be extracted is stored
    :param year_column:  Name of the column where the year is stored
    :param kwargs: Kwargs for pandas read csv, here one specifies the separators and numerical symbols in the source.
    :return: a list of values extracted
    """
    data = pd.read_csv(path, **kwargs)
    value = data[data[year_column].isin(years)][value_column]
    return value.to_list()

def aggregated_values(years, path, date_column, value_column, **kwargs):
    """
    Similar to basic values, but for inputs that are not reported in yearly values, it aggregates days and months
    :param years: List of years to be extracted
    :param path: Path of the Data source
    :param value_column: Name of the column where the value to be extracted is stored
    :param year_column:  Name of the column where the year is stored
    :param kwargs: Kwargs for pandas read csv, here one specifies the separators and numerical symbols in the source.
    :return: a list of values extracted
    """
    df = pd.read_csv( path, **kwargs )
    df[date_column] = pd.to_datetime( df[date_column] )
    #df[value_column] = df[value_column].map(atof)
    df_agg = df.groupby( df[date_column].dt.year )[value_column].mean().reset_index().rename(
        columns={date_column : 'Year', value_column: 'Rate'} )
    value = df_agg[df_agg["Year"].isin( years )]["Rate"]
    return value.to_list()

def rolled_values(years, path, date_column, value_column, **kwargs):
    """
    Experimental aggregation which aggregates values using rolling averages.
    :param years: List of years to be extracted
    :param path: Path of the Data source
    :param value_column: Name of the column where the value to be extracted is stored
    :param year_column:  Name of the column where the year is stored
    :param kwargs: Kwargs for pandas read csv, here one specifies the separators and numerical symbols in the source.
    :return: a list of values extracted
    """
    data = pd.read_csv( path, **kwargs)
    try:
        data[date_column] = pd.to_datetime(data[date_column], format = "%d.%m.%Y")
        df_agg = data.groupby( data[date_column].dt.year )[value_column].mean().reset_index().rename(
            columns={date_column: 'Year'})
    except:
        df_agg = data.rename(columns = {date_column : "Year"})
    df_agg[value_column] = df_agg[value_column].rolling(2).mean().fillna(df_agg[value_column][0])
    value = df_agg[df_agg["Year"].isin( years )][value_column]
    return value.to_list()

# Index map, this is useful to avoid going to the files over and over, thus saving commputing power
def create_index_map(years, basic_indexes = basic_indexes, aggregated_indexes = aggregated_indexes, rolled_indexes = rolled_indexes):
    """
    Using a given set of sources and years createss a table that can be used as a source for the indexes in the conversion
    of values
    :param years: List of years
    :param basic_indexes: Dictionary of basic indexes
    :param aggregated_indexes:  Dictionary of aggregated indexes
    :param rolled_indexes: Dicrionary of rolled indexes
    :return: Dataframe with indexes mapped to the given year
    """
    mapped = pd.DataFrame()
    mapped["YEAR"] = years
    for index in basic_indexes:
        mapped[index] = basic_values(years, **basic_indexes[index])
    for index in aggregated_indexes:
        mapped[index] = aggregated_values(years, **aggregated_indexes[index])
    for index in rolled_indexes:
        mapped[index] = rolled_values( years, **rolled_indexes[index] )


    return mapped.sort_values("YEAR")

def convert_value(value, idx_map, year_ref, year_new ,index):
    """
    Converts given value from the reference year to the desired year using the given index and index map
    :param value: Float with the original value
    :param idx_map: Index map generated with create_index_map
    :param year_ref: Year of the reference value
    :param year_new: Desired yeaar
    :param index: Desired Index name
    :return:  New value
    """
    ref_idx = idx_map.loc[(idx_map["YEAR"] == year_ref), index].values[0]
    new_idx = idx_map.loc[(idx_map["YEAR"] == year_new), index].values[0]
    return value * new_idx / ref_idx


def change_currency(value, idx_map, year, direction):
    """
    Special kind of transformation that converts values in a given year, works only between euro and dollar
    :param value: original value
    :param idx_map: index map from create_index_map
    :param year: Year of transformation
    :param direction: "EURUSD" as default to convert euroes into usd, "USDEUR" to do the inverese
    :return: New Value
    """
    change = idx_map.loc[(idx_map["YEAR"] == year), "EURUSD"].values[0]
    if direction == "USDEUR":
        change = 1/change

    return value * change


def _print_index_map(index_map, fig_path):
    """
    Helper function to create index map figure
    :param index_map:
    :return:
    """
    index_map.iloc[:,1:] = index_map.iloc[:,1:].div(index_map.iloc[0,1:])

    # with plt.style.context( 'Solarize_Light2' ):
    fig , ax = plt.subplots(figsize = (11.6,4.0))
    index_map.plot(x = "YEAR", y = index_map.columns[1:], cmap = "Set2", ax =ax)
    # ax.set_title("Index development in relation to Reference Year {}".format(index_map.YEAR.min()))
    ax.set_xticks(np.arange(index_map.YEAR.min(), index_map.YEAR.max()+1))
    ax.set_xlabel( "Year", fontsize=20)
    ax.set_ylabel( "Relative Index", fontsize  = 20 )
    ax.set_xlim( [index_map.YEAR.min(), index_map.YEAR.max()] )
    ax.set_ylim([0, 5])
    ax.grid(axis = "y", c = "gainsboro")
    #plt.gca().set_aspect( "equal" )
    ax.set_facecolor( 'white' )
    # Shrink current axis by 20%
    box = ax.get_position()
    # ax.set_position( [box.x0, box.y0, box.width * 0.95, box.height] )
    ax.tick_params( axis='both', which='major', labelsize=10 )
    # Put a legend to the right of the current axis
    L = ax.legend( loc='center left', bbox_to_anchor=(1, 0.5))
    L.get_texts()[3].set_text('Coal')
    L.get_texts()[4].set_text( 'EUR-USD' )
    L.get_texts()[5].set_text( 'Gas' )
    plt.tight_layout()
    fig.savefig( fig_path )
    plt.show()


def _export_index_map_as_latex(idx_map, path):
    idx_map = idx_map.rename(columns = {"YEAR" : "Year",
                                        "COALIDX" : "Coal ",
                                        "NGIDX": "Natural Gas",
                                        "EURUSD": "EUR-USD"})
    print(idx_map.to_latex(index = False, float_format = "%.2f"))

# idx_map = create_index_map(years, basic_indexes, aggregated_indexes, rolled_indexes)
def index_generator():
    return create_index_map(years, basic_indexes, aggregated_indexes, rolled_indexes)
if __name__ == "__main__":
    print(idx_map)