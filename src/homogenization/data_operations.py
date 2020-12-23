import powerplantmatching as pm
import pandas as pd
import logging
import ast
import math
import numpy as np
from src.tools.config_loader import Configuration
config = Configuration.get_instance()
pd.set_option('display.max_columns', None)
io = config["IO"]

# Power Plant Matching
CONVENTIONAL = ['Hard Coal', 'Natural Gas', 'Lignite', 'Oil']
BIOFUELS = ["Bioenergy"]


class DataSource:
    def __init__(self, data=None, local_path=None):
        self.data = data
        self.local_path = local_path

    def get_data(self):
        return self.data

    def set_data(self, dataframe):
        self.data = dataframe

    def fetch_from_local(self, **kwargs):
        data = pd.read_csv(self.local_path, **kwargs)
        return data

    def export_data(self, path):
        self.data.to_csv(path, index=True)

    def __str__(self):
        return self.data.__str__()

    @classmethod
    def from_file(cls, path, **kwargs):
        instance = cls(local_path=path)
        instance.set_data(instance.fetch_from_local(**kwargs))
        return instance


class OPSD(DataSource):
    def __init__(self, de=True):
        if de:
            super().__init__(local_path=io["LOCAL_OPSD_DE_PATH"])
        else:
            super().__init__(local_path=io["LOCAL_OPSD_EU_PATH"])

        self.set_data(self.fetch_from_local())


class PowerPlantMatching(DataSource):

    def __init__(self, local=True):
        super().__init__(local_path=io["LOCAL_PPM_PATH"])
        if local:
            try:
                self.set_data(self.fetch_from_local(index_col="id"))
            except FileNotFoundError:
                msg = "The local file \"{}\" does not exist, please fetch from URL".format(io["LOCAL_PPM_PATH"])
                logging.warning(msg)
                self.data = None
        else:
            self.set_data(self.fetch_ppm_from_url())
            self.export_data(self.local_path)

    @staticmethod
    def fetch_ppm_from_url():
        data = pm.powerplants(from_url=True)
        return data

    @classmethod
    def filter_fuels(cls, fuels="conventional"):
        if fuels == "conventional":
            fuels = CONVENTIONAL
        elif fuels == "biofuels+conventional":
            fuels = BIOFUELS + CONVENTIONAL
        elif fuels == "biofuels":
            fuels = BIOFUELS
        instance = cls(True)
        instance.set_data(instance.data[instance.data.Fueltype.isin(fuels)])
        return instance

    @classmethod
    def opsd_efficiency(cls, fuels="conventional"):
        def extract_column(column, labels, supp_df):
            sub_df = supp_df[supp_df.id.isin(labels)]
            vals = sub_df[column].values
            if len(vals) == 0:
                return np.nan
            return "operating" if any(vals == "operating") else "shutdown"

        if fuels == "conventional":
            fuels = CONVENTIONAL
        elif fuels == "biofuels+conventional":
            fuels = BIOFUELS + CONVENTIONAL
        elif fuels == "biofuels":
            fuels = BIOFUELS

        instance = cls(os.path.isfile(io["LOCAL_PPM_PATH"]))
        instance.set_data(instance.data[instance.data.Fueltype.isin(fuels)])

        main_data = instance.get_data()
        support_data = OPSD().data

        main_data['match_id'] = main_data.projectID.apply(
            lambda x: ast.literal_eval(x)['OPSD'] if 'OPSD' in ast.literal_eval(x).keys() else [])
        main_data["Efficiency"] = 0
        main_data["Efficiency"] = main_data["match_id"].apply(lambda x:
                                                              support_data[
                                                                  support_data.id.isin(x)].efficiency_data.mean())
        main_data["Efficiency"] = main_data["Efficiency"].apply(lambda x: 0 if math.isnan(x) else x)
        main_data["Operating"] = ""
        main_data["Operating"] = main_data["match_id"].apply(lambda x: extract_column("status", x, support_data))
        instance.set_data(main_data)

        return instance
