from src.tools.config_loader import Configuration
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.font_manager
import cartopy.crs as ccrs
import cartopy

pd.set_option('display.max_columns', None)
matplotlib.font_manager.findSystemFonts(fontpaths=None, fontext='ttf')
config = Configuration.get_instance()

file_path = config["IO"]["complete_set_path"]
local_config = config["CostCurveConfig"]

figsize = (8, 12)
bot_left = (32, -16)
bot_right = (32, 40)
top_left = (84, -16)
top_right = (84, 40)


# Create class to contain the curve and plot it maybe


def plot_point_distribution(cost_distribution_frame, **kwargs):
    if cost_distribution_frame.geo:
        cost_distribution_frame.switch()
    df = cost_distribution_frame.data
    with sns.axes_style('darkgrid'):
        sub_kw = {'projection': ccrs.PlateCarree()}
        fig, ax = plt.subplots(figsize=figsize, subplot_kw=sub_kw)
        sns.scatterplot(x="lon", y="lat", hue="cost",
                        sizes=(10, 400), size="amount", data=df, ax=ax,
                        palette="gnuplot", style="source", **kwargs)

        ax.set_extent((-16, 40) + (32, 74),
                      crs=ccrs.PlateCarree())
        resolution = '50m'
        ax.coastlines(linewidth=0.4, zorder=-1, resolution=resolution)
        border = cartopy.feature.BORDERS.with_scale(resolution)
        ax.add_feature(border, linewidth=0.3)
        ax.outline_patch.set_visible(False)
        land = cartopy.feature.LAND.with_scale(resolution)
        ocean = cartopy.feature.OCEAN.with_scale(resolution)
        ax.add_feature(ocean, facecolor='cornflowerblue', alpha=0.8)
        ax.add_feature(land, facecolor='bisque', alpha=1.0)

        frame = plt.legend(bbox_to_anchor=(1.0, 0.5), loc='center left', fancybox=True).get_frame()
        frame.set_linewidth(0.5)
        frame.set_facecolor('white')
        frame.set_edgecolor('black')

        ax.set_title("Cost of carbon capture for European Countries ", fontname="Courier New")
        plt.setp(ax.get_legend().get_texts(), fontname="Courier New")
        return fig, ax
