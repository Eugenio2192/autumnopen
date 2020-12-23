from src.tools.config_loader import Configuration
from src.homogenization.data_operations import DataSource
from src.curveproduction.plot import plot_point_distribution
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import warnings
config = Configuration.get_instance()
pd.set_option('display.max_columns', None)
io = config["IO"]
costcurveconfig = config["CostCurveConfig"]

nuts_paths = {0: io["countries_borders_path"],
              1: io["nuts_1_path"],
              2: io["nuts_2_path"],
              3: io["nuts_3_path"]}

test_output_path = io["test_output_csv"]

DEFAULT_COLUMNS = ["id", "source", "geographical_label", "year", "production_capacity", "amount", "cost"]

column_map_pp = {"id": "id",
                 "source": "Fuel",
                 "geographical_label": "Country",
                 "year": "DateIn",
                 "production_capacity": "CapacityMW",
                 "amount": "AmountCapturedMtY",
                 "cost": "CostOfCarbonCaptureEURtonCO2",
                 "lat": "lat",
                 "lon": "lon"}

column_map_cement = {"id": "ID",
                     "source": "Source",
                     "geographical_label": "Country",
                     "year": "Year",
                     "production_capacity": "Production",
                     "amount": "AmountCapturedMtY",
                     "cost": "CostOfCarbonCaptureEURtonCO2",
                     "lat": "Latitude",
                     "lon": "Longtitude"}

column_map_iron = {"id": "ID",
                   "source": "Source",
                   "geographical_label": "Country",
                   "year": "Year",
                   "production_capacity": "CapacityM",
                   "amount": "AmountCapturedMtY",
                   "cost": "CostOfCarbonCaptureEURtonCO2",
                   "lat": "DD Latitude",
                   "lon": "DD Longitude"}


def poly_case(case):
    poly = gpd.read_file(nuts_paths[case])
    if case == 0:
        ID = "NUTS_ID"
    else:
        ID = "NUTS_ID"
    poly = poly.rename(columns={ID: "MAIN_ID"})
    return poly


def do_geographical_join_nuts(data, level=0):
    assert isinstance(data, gpd.GeoDataFrame), "input must be a GeoDataFrame with points"

    poly = poly_case(level)
    joined = gpd.sjoin(data, poly, op="intersects")
    return joined


class CostDistribution(DataSource):
    # Call with super, take a look
    def __init__(self, data=None, column_map=None, local_path=None, geo=False, input_geo=False):
        super().__init__(data=data, local_path=local_path)
        self.differentiate_input(data, column_map, geo, input_geo)
        self.level = None
        self.geo = geo

    def differentiate_input(self, data=None, column_map=None, geo=False, input_geo=False):
        if data is not None:
            self.data = self.create_spatial_cost_distribution_dataframe(data, column_map, input_geo)
        else:
            self.data = self.fetch_from_local()
        if input_geo:
            if geo:
                self.geo = input_geo
            else:
                self.data = self.switch_to_df(self.data)
        else:
            if geo:
                self.data = self.switch_to_geo(self.data)

    def __repr__(self):
        if self.geo:
            string = "Cost potential distribution in geodataframe form"
        else:
            string = "Cost potential distribution in dataframe form"
        return string

    def match_this_nuts_regions(self, level):
        assert self.geo, "Data should be in a GeoDataFrame form"
        self.level = level
        self.data = self.match_nuts_region(self.data, level)

    # pseudo class method
    def aggregate(self, geo=True):
        df = self.data.groupby(["source", "geographical_label"]).agg({"amount": "sum",
                                                                      "cost": "mean",
                                                                      "year": "max",
                                                                      "production_capacity": "sum"})
        df = df.reset_index()
        poly = poly_case(self.level)
        poly["geometry"] = poly.centroid
        poly = poly.set_index("MAIN_ID")
        df = df.set_index("geographical_label")
        df = df.join(poly)
        df = df.reset_index()
        df = df.rename(columns={"index": "geographical_label"})
        df = df[["source", "geographical_label", "year", "production_capacity", "amount", "cost", "geometry"]]
        df = df.reset_index()
        df = df.rename(columns={"index": "id"})
        column_map = {x: y for x, y in zip(df.columns, df.columns)}
        gdf = gpd.GeoDataFrame(df)
        output = CostDistribution(gdf, column_map, geo=geo, input_geo=True)
        return output

    def export_data(self, path, geo):
        if geo:
            assert path.split(".")[-1] == "shp", "File must end with .shp"
            self.data.to_file(path)
        else:
            assert path.split(".")[-1] == "csv", "File must end with .csv"
            super().export_data(path)

    def fetch_from_local(self, **kwargs):
        ending = self.local_path.split(".")[-1]
        if ending == "csv":
            data = pd.read_csv(self.local_path, **kwargs)
        elif ending == "shp":
            data = gpd.read_file(self.local_path, **kwargs)
        else:
            raise ValueError(f'Ending {ending} should be either csv or shp')
        return data

    def switch(self):
        if self.geo:
            self.data = self.switch_to_df(self.data)
            self.geo = not self.geo
        else:
            self.data = self.switch_to_geo(self.data)
            self.geo = not self.geo

    def plot(self, **kwargs):
        plot_point_distribution(self, **kwargs)
        plt.show()

    @classmethod
    def from_file(cls, path, geo, **kwargs):
        ending = path.split(".")[-1]
        if ending == "csv":
            input_geo = False
            default_columns = DEFAULT_COLUMNS + ["lat", "lon"]
            column_map = {x: y for x, y in zip(default_columns, default_columns)}
        else:
            input_geo = True
            default_columns = DEFAULT_COLUMNS + ["geometry"]
            column_map = {x: y for x, y in zip(default_columns, default_columns)}
            column_map["geographical_label"] = "geographic"
        instance = cls(local_path=path, column_map=column_map, input_geo=input_geo, geo=geo)
        return instance

    @staticmethod
    def match_nuts_region(df, level):
        if level == -1:
            output = df
            output["geographical_label"] = "EURO"
            return output
        joined = do_geographical_join_nuts(df, level)
        output = joined[["source", "MAIN_ID", "year", "production_capacity", "amount", "cost", "geometry"]]
        output = output.rename(columns={"MAIN_ID": "geographical_label"})
        return output

    @staticmethod
    def create_spatial_cost_distribution_dataframe(df, column_map, input_geo=False):
        if input_geo:
            default_columns = DEFAULT_COLUMNS + ["geometry"]
        else:
            default_columns = DEFAULT_COLUMNS + ["lat", "lon"]
        assert all([default_columns[i] == list(column_map.keys())[i] for i in range(len(default_columns))]), \
            "The column map should match the default columns of the structure"
        inv_map = {v: k for k, v in column_map.items()}
        idf = df.rename(columns=inv_map)
        sdf = idf[default_columns]
        if input_geo:
            sdf = gpd.GeoDataFrame(sdf, crs=costcurveconfig["CRS"])
        sdf = sdf.set_index("id")
        return sdf

    @staticmethod
    def switch_to_geo(df):
        output = gpd.GeoDataFrame(
            df, geometry=gpd.points_from_xy(df.lon, df.lat))
        output.crs = costcurveconfig["CRS"]
        output = output.drop(columns=["lat", "lon"])
        return output

    @staticmethod
    def switch_to_df(gdf):
        gdf.to_crs(costcurveconfig["projCRS"])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            gdf["lon"] = gdf.centroid.x
            gdf["lat"] = gdf.centroid.y
        if "geographic" in gdf.columns:
            gdf = gdf.rename(columns={"geographic": "geographical_label",
                                      "production": "production_capacity"})
        output = gdf[DEFAULT_COLUMNS[1:] + ["lat", "lon"]]
        gdf.to_crs(costcurveconfig["CRS"])
        return output



