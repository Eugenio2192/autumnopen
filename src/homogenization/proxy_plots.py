import matplotlib.pyplot as plt
from matplotlib import rc
from src.homogenization.proxy_efficiency import ppm_proxy_efficiency

rc('font', **{'family': 'serif', 'serif': ['Palatino']})
rc('text', usetex=True)


def plot_predicted_efficiencies_vs_capacities(df, ax):
    grouped = df.groupby('Fueltype')
    cmap = ['salmon', 'dodgerblue', 'forestgreen']
    colors = dict(zip(grouped.groups.keys(), cmap))
    with plt.style.context('seaborn-darkgrid'):
        for key, group in grouped:
            group[group.Efficiency != 0].plot(ax=ax, kind='scatter', x='Capacity', y='Efficiency', label=key,
                                              color=colors[key], alpha=0.8, marker="*", s=100)
            group[group.Efficiency == 0].plot(ax=ax, kind='scatter', x='Capacity', y='predicted_efficiency', label=key,
                                              color=colors[key], alpha=0.4)

        ax.set_xlabel('Capacity [MW]')
        ax.set_ylabel('Efficiency [KJ Electricity / KJ Heat]')
        ax.legend(["Hard coal data", "Hard coal predicted", "Lignite data", "Lignite predicted", "Natural gas data",
                   "Natural gas predicted"])
        ax.set_title('Capacity vs existing and predicted efficiency data', fontweight='bold')
        return ax


def plot_predicted_efficiencies_vs_years(df, ax):
    grouped = df.groupby('Fueltype')
    cmap = ['salmon', 'dodgerblue', 'forestgreen']
    colors = dict(zip(grouped.groups.keys(), cmap))
    with plt.style.context('seaborn-darkgrid'):
        for key, group in grouped:
            group[group.Efficiency != 0].plot(ax=ax, kind='scatter', x='YearCommissioned', y='Efficiency', label=key,
                                              color=colors[key], alpha=0.8, marker="*", s=100)
            group[group.Efficiency == 0].plot(ax=ax, kind='scatter', x='YearCommissioned', y='predicted_efficiency',
                                              label=key,
                                              color=colors[key], alpha=0.4)

        ax.set_xlabel('Commission year')
        ax.set_ylabel('Efficiency [KJ Electricity / KJ Heat]')
        ax.legend(["Hard coal data", "Hard coal predicted", "Lignite data", "Lignite predicted", "Natural gas data",
                   "Natural gas predicted"])
        ax.set_title('Commission year vs existing and predicted efficiency data', fontweight='bold')

        return ax


def plot_predicted_efficiencies_vs_fuels(df, ax):
    grouped = df.groupby('Fueltype')
    cmap = ['salmon', 'dodgerblue', 'forestgreen']
    colors = dict(zip(grouped.groups.keys(), cmap))
    with plt.style.context('seaborn-darkgrid'):
        for key, group in grouped:
            group[group.Efficiency != 0].plot(ax=ax, kind='scatter', x='Fueltype', y='Efficiency', label=key,
                                              color=colors[key], alpha=0.8, marker="*", s=100)
            group[group.Efficiency == 0].plot(ax=ax, kind='scatter', x='Fueltype', y='predicted_efficiency', label=key,
                                              color=colors[key], alpha=0.4)

        ax.set_xlabel('Fuel type')
        ax.set_ylabel('Efficiency [KJ Electricity / KJ Heat]')
        ax.legend(["Hard coal data", "Hard coal predicted", "Lignite data", "Lignite predicted", "Natural gas data",
                   "Natural gas predicted"])
        ax.set_title('Fuel type vs existing and predicted efficiency data', fontweight='bold')

        return ax
