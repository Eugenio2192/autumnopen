from src.curveproduction.geo_distribution_data import CostDistribution
from src.tools.algorithms import list_combination
import matplotlib.pyplot as plt
import numpy as np


class CurveCollection:
    def __init__(self, distribution, region="all", source="all"):
        assert isinstance(distribution, CostDistribution), "input should be a CostDistribution data source"
        self.distribution = distribution
        self.metadata = {"region": region,
                         "sources": source}
        self.curves = []

    def __repr__(self):
        return "Curve collection,  Regions: {}, Sources: {}".format(self.metadata["region"],
                                                                    self.metadata["sources"])

    @staticmethod
    def create_curve_collection(distribution, region_list, source_list):
        pairs = list_combination(region_list, source_list)
        collection = []
        for pair in pairs:
            curve = CostCurve.from_distribution(distribution, pair[0], pair[1])
            collection.append(curve)
        return collection

    def plot(self, ax=None):
        if ax:
            ax = ax
        else:
            fig, ax = plt.subplots(figsize=(12, 10))
        self.plot_curve_collection(ax, *self.curves)
        return ax

    @staticmethod
    def plot_curve_collection(ax, *collection):
        lines = ["solid", "dashdot", "dotted", "dashed"]
        regions = set([curve.metadata["region"] for curve in collection])
        colors = get_cmap(len(regions))
        max_lim = max([cu.curve.amount.max() for cu in collection])
        for j, region in enumerate(regions):
            region_curves = [curve for curve in collection if curve.metadata["region"] == region]
            sort_values = [curve.curve.cost.min() for curve in region_curves]
            sort_index = np.argsort(sort_values)
            sorted_curves = [region_curves[i] for i in sort_index]
            sorted_labels = ["{0} {1}".format(region_curves[i].metadata["source"], region_curves[i].metadata["region"])
                             for
                             i in sort_index]
            for i in range(len(sorted_curves)):
                if i < len(sorted_curves) - 1:
                    if sorted_curves[i].curve["cost"].max() > sorted_curves[i + 1].curve["cost"].min():
                        sorted_curves[i].curve = sorted_curves[i].curve[
                            sorted_curves[i].curve["cost"] <= sorted_curves[i + 1].curve["cost"].min()]
                    sorted_curves[i + 1].curve["amount"] = sorted_curves[i + 1].curve["amount"] + \
                                                           sorted_curves[i].curve["amount"].max()
                    sorted_curves[i].curve = sorted_curves[i].curve.append(sorted_curves[i + 1].curve.iloc[0])
                    if max_lim < sorted_curves[i + 1].curve.amount.max():
                        max_lim = sorted_curves[i + 1].curve.amount.max()
            for i, curve in enumerate(sorted_curves):
                ax = curve.plot(ax, linestyle=lines[np.mod(i, len(sorted_curves))], color=colors(j))

            ax.set_xlim([0, max_lim])
            ax.grid()
            ax.set_facecolor('whitesmoke')
            ax.set_xlabel("Captured carbon (Mt/y)")
            ax.set_ylabel("Cost (€/t)")
            ax.set_title("Cost of captured carbon")
            frame = plt.legend(bbox_to_anchor=(1.0, 0.5), loc='center left', fancybox=True).get_frame()
            frame.set_linewidth(0.5)
            frame.set_facecolor('white')
            frame.set_edgecolor('black')

    @classmethod
    def from_boundaries(cls, distribution, region_list, source_list):
        instance = cls(distribution)
        instance.curves = cls.create_curve_collection(distribution, region_list, source_list)
        instance.metadata["region"] = ", ".join(region_list)
        instance.metadata["sources"] = ", ".join(source_list)
        return instance


class CostCurve:
    def __init__(self, data, region="all", source="all"):
        self.data = data
        self.metadata = {"region": region,
                         "source": source}
        self.curve = self.create_curve()

    def __repr__(self):
        return "{} curve from {}".format(self.metadata["source"], self.metadata["region"])

    @classmethod
    def from_distribution(cls, distribution, region="all", source="all"):
        assert isinstance(distribution, CostDistribution), "input should be a CostDistribution data source"
        data = CostCurve.extract_data_from_distribution(distribution, region, source)
        return cls(data, region, source)

    @staticmethod
    def extract_data_from_distribution(distribution, region="all", source="all"):
        data = distribution.data
        if region != "all":
            data = data[data.geographical_label == region]
        if source != "all":
            if source == "Coals":
                data = data[data["source"].isin(["Hard Coal", "Lignite"])]
            elif source == "Fossil Fuels":
                data = data[data["source"].isin(["Hard Coal", "Lignite", "Natural Gas"])]
            else:
                data = data[data["source"] == source]
        return data

    def create_curve(self):
        df = self.data
        df = self.sort_values(df)
        df = self.add_cumsum_col(df)
        df = self.sort_dataframe(df)
        df = df.rename(columns={"value": "amount"})
        return df

    def plot(self, ax, **kwargs):
        if "label" in kwargs:
            pass
        else:
            kwargs["label"] = "{0} in {1}".format(self.metadata["source"], self.metadata["region"])

        self.curve.plot("amount", "cost", ax=ax, **kwargs)
        ax.grid()
        ax.set_facecolor('whitesmoke')
        ax.set_xlabel("Captured carbon (Mt/y)")
        ax.set_ylabel("Cost (€/t)")
        return ax

    def plot_sc(self, ax, year, **kwargs):
        self.curve.plot("amount", "cost", ax=ax,
                        label=year, **kwargs)
        ax.grid()
        ax.set_facecolor('whitesmoke')
        ax.set_xlabel("Captured carbon (Mt/y)")
        ax.set_ylabel("Cost (€/t)")
        return ax

    @staticmethod
    def sort_values(df):
        df = df.sort_values("cost").reset_index()
        return df

    @staticmethod
    def add_cumsum_col(df):
        df["cumsum"] = df.amount.cumsum()
        df["shift_sum"] = df["cumsum"].shift()
        df.loc[0, "shift_sum"] = 0
        df = df.rename(columns={"cumsum": "upper", "shift_sum": "lower"})
        df = df.drop(columns=["amount"])
        df = df[["source", "cost", "upper", "lower"]]
        df = df.melt(id_vars=["source", "cost"]).reset_index().drop(columns=["index"])
        return df

    @staticmethod
    def sort_dataframe(df):
        df = df.sort_values(["cost", "value"]).reset_index().drop(columns=["index"])
        return df


class ScenarioCollection(CurveCollection):
    def __init__(self, distribution, years="all", source="all"):
        super().__init__(distribution, region="all", source=source)
        self.metadata["years"] = years


def get_cmap(n, name='Paired'):
    """Returns a function that maps each index in 0, 1, ..., n-1 to a distinct
    RGB color; the keyword argument name must be a standard mpl colormap name."""
    return plt.cm.get_cmap(name, n)
