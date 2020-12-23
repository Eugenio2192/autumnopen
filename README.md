# Cost Potential Curves from Captured CO2 Sources

A tool to assign costs to geographically distribuited CO2 sources.

This project is produced as part of the Master Thesis of Eugenio Arellano

# Installation 

To install, clone the repository in your computer by using git or downloading it. It is recommended that an environment virtual environment is created for the project,either from conda or any other package manager. Once you have it in your system install the dependencies using conda doing:

```console
conda install yaml pandas geopandas catorpy seaborn scikit-learn statsmodels scipy dash plotly -c conda-forge
```

Or with pip using:
```console
pip install yaml pandas geopandas catorpy seaborn scikit-learn statsmodels scipy dash plotly
```

Once the dependencies are installed, the background operations have to be fulfilled. First make sure you have all the data necessary by following the instructions in the documentation build the data directory tree by running 

```python
from src.tools.basedirs import create_directory_tree
create_directory_tree()
```

What you have to do next varies depending on your data availibility, refer to the data procuring section of th edocumentation.

field returns a dataset filtered for said countries.

Once you have the data proceed to initialize the api so the data is generated.

```python
from src. api import *
```

```
>>>initialize()
2020-11-30 14:02:20 INFO     Starting harmonization
2020-11-30 14:02:23 INFO     Calculating cost values
2020-11-30 14:02:23 INFO     Creating power plant input file
2020-11-30 14:02:29 INFO     Creating power plant cost potential file
2020-11-30 14:02:36 INFO     Creating iron and steel cost potential file
2020-11-30 14:02:36 INFO     Creating cement cost potential file
```

If this worked with no errors then you are good to do the operations, note that if you do not have t he iron and steel data, the initialization won't look for the values.

# Basic Usage

## Distribution Data

After importing the api functions, to get the general processed power plant cost potential dataset run:

```
>>>Distribution = cost_emission_distribution("basic")
```
Doing so will store a Distrbution instance from where you can extract the data running:

```
>>>data = Distribution.data
```
This will return a pandas dataframe. You can also plot the distribution in a map simply using the following instruction:

```
>>>Distribution.plot()
```
![basic map](/documentation/source/basic_map.png)

## Cost Potential Curves
Before you can start working with cost potential curves you need to import the curve module and matplotlib and create a distribution object.

```python
from src.curveproduction.cost_potential_curve import *
import matplotlib.pyplot as plt
Distribution = cost_emission_distribution("basic")
```

Once you have done this you can create a single curve.

```python
fig, ax = plt.subplots()
data = distribution.data
european_curve = CostCurve(data)
european_curve.plot(ax)
```
![basic map](/documentation/source/basic_curve.png)

But maybe it is more interesting for you to see some granularity, for doing so we use the CurveCollection class. The way it works is by calling a constructor giving ISO codes of the territories we want to work with and the carbon sources to consider.

```python
fig , ax = plt.subplots(figsize=(12,10))
collection = CurveCollection.from_boundaries(distribution, ["DE", "ES", "IT"], ["Hard Coal", "Natural Gas", "Lignite"])
collection.plot(ax)
```

![basic map](/documentation/source/granular_curve.png)

## Scenario representations

The scenarios used in this tool are built based on the GECO scenarios, there are 3 of them a “Reference” scenario, “1.5°C” scenario and a “2C_M” scenario. To see the curves run:

```python
fig, ax = plt.subplots(figsize=(12,8))
produce_scenario_collection(scenarios, "Reference", ax)
```

![basic map](/documentation/source/scenarios.png)