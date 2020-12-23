Getting the necessary data
==========================

Before everything, make sure you have built the necessary directories using the function availible in the tools directory.

..  code-block:: python

	from src.tools.basedirs import create_directory_tree
	create_directory_tree()


EUROSTATS data
--------------

In order to be able to perform the aggregation operations and geographical labeling in this tool, 
geographical information is needed. This information is provided by EuroGraphics through the Eurostat 
website for non commercial uses. 
Given unknown restrictions on the redistribution of this data it was decided to keep it out of the repository. 
The user will need to download it by themselves and put them in the folder. 
Here are the detailed instructions for doing so:

First, go to the data website found `the eurostat geodata website <https://ec.europa.eu/eurostat/web/gisco/geodata/reference-data/administrative-units-statistical-units/nuts>`_

and download the 2021 SHP data in the 1:1 Million resolution by clicking on it. 
Once you have the data, extract and unpack the following files into the Data\\CostPotentialCurves\\Input\\NUTS folder:

NUTS_RG_01M_2021_4326_LEVL_0

NUTS_RG_01M_2021_4326_LEVL_1

NUTS_RG_01M_2021_4326_LEVL_2

NUTS_RG_01M_2021_4326_LEVL_3

OPSD data
---------

There is two datasets from the Open Energy System that are necessary for the correct functioning of the tool: the european
conventional power plant dataset and the german one, both of them can be found in the 
`OPSD website <https://data.open-power-system-data.org/conventional_power_plants/2020-10-01>`_

Download the csv files and put them  in:
"Data\\GeographicalDataHomogenization\\Input"

FRESNA data
-----------

The power plant matching data will be downloaded automatically if you don't have it installed, just make sure you have installed
their api using pip.

.. prompt:: bash

	pip install powerplantmatching
	

Industrial Data
---------------

If you don't have your own industrial data please email the authors to see options to obtain your own.


Scenario Data
-------------

The scenario development is done using the Global Energy and Climate Outlook from the European Union. The data
is availible in their `website <https://ec.europa.eu/jrc/en/geco/visualisation>`_
You can download the necessary data by going to Energy>Production then clicking the download button at the bottom right.

Once you have downloaded the data, just place it in the  Data/scenarios/input directory.


Index data
-----------
All the index values have associated paths in the config file, please locate the files in the corresponding paths with
the desired names or change the desired path, this last option is not recommended to avoid undesirable results

CEPCI
^^^^^

The index data provided has varying sources. For the CEPCI data was compiled by u/r_m_castro in the following
`reddit post <https://www.reddit.com/r/ChemicalEngineering/comments/fu94v2/does_anyone_have_access_to_the_chemical/>`_
the values
were properly validated by looking at the referenced sources, this was converted to a .csv file which is provided in the 
repository.

Directory: CaptureCostHarmonization/input/indexes/CEPCI.csv

Coal
^^^^

The coal cost index was calculated based on the World Bank open data found in 
`their website <https://www.worldbank.org/en/research/commodity-markets>`_
there is special instructions to download these values, download the zip file at charts and data files and extract
the annual commodity prices file, from there copy the values of the coal prices into a separate
csv file and store it in the corresponding folder.

Directory: CaptureCostHarmonization/input/indexes/coal_index_WB.csv

Natural Gas
^^^^^^^^^^^

For the natural gas price developments the Henry Hub Index is used. This can be found reported in the `Energy Information Administration <https://www.eia.gov/dnav/ng/hist/rngwhhdm.htm>`_.
The used values are an average of the yearly reports.

Directory: CaptureCostHarmonization/input/indexes/natural_gas_hh.csv

IHS Indexes
^^^^^^^^^^^

The energy cost and technology indexes were estimated based on information published in the 
`IHS Upstream Cost Indexes <https://ihsmarkit.com/Info/cera/ihsindexes/index.html>`_
these values can't be extracted directly so tabulate them yourself or send the authors an email.
By default the tool uses CEPCI for all transformations so doing this is not absolutely necessary.

Directory: CaptureCostHarmonization/input/indexes/IHS.csv

Currency Exchange
^^^^^^^^^^^^^^^^^ 

The currency exchange data can be easily found in `here <http://www.ecb.int/stats/eurofxref/eurofxref-hist.zip>`_
download it and place it in  the corresponding folder.

Directory: CaptureCostHarmonization/input/indexes/eurofxref-hist.csv


Current Fuel cost
-----------------

The values for the fuel costs are obtained from `the U.S. Energy Information Administration <https://www.eia.gov/coal/markets/>`_ and other 
similar sources, the emission factors are matched using `this report <https://www.umweltbundesamt.de/sites/default/files/medien/1968/publikationen/co2_emission_factors_for_fossil_fuels_correction.pdf>`_ 
and are collected in the followning json file, save it and place it in the CaptureCostHarmonization/input/fuel_data.json directory.

.. code-block:: JSON

	 {
	  "Illinois_6_ton": {
		"Type": "hard_coal",
		"HHV_GJ": 25.35,
		"LHV_GJ": 24.12,
		"Cost_2019_USD" : 34.473,
		"Cost_2020_USD" : 31.29,
		"Emission_Factor_KG_KJ" : 0.000094
	  },
	  "powder_river_basin_ton": {
		"Type": "lignite",
		"HHV_GJ": 11.86,
		"LHV_GJ": 10.07,
		"Cost_2019_USD" : 10.43,
		"Cost_2020_USD" : 10.43,
		"Emission_Factor_KG_KJ" : 0.000110
	  },
	  "natural_gas_m3": {
		"Type": "natural_gas",
		"HHV_GJ": 40,
		"LHV_GJ": 36,
		"Cost_2019_USD":84.3,
		"Cost_2020_USD": 62.26,
		"Emission_Factor_KG_KJ" : 0.000056
	  },
	  "black_liqor_ton": {
		"Type": "bioenergy",
		"HHV_GJ": 21,
		"LHV_GJ": 19.3,
		"Cost_2019_USD": 63.0,
		"Cost_2020_USD": 63.0,
		"Emission_Factor_KG_KJ" : 0.000071
	  }
	}


Disclaimer: All of these indexes are aggregated, estimated  or calculated.

If you think you have more realiable values modify the files in the index
folder and then assign your new file to the corresponding entry in the config file. You will need to assign the column names in the "cost_transformation_functions.py"
to match the ones in your new index. If your index is not aggregated by year, add it to the aggregated index dictionary in said file, otherwise add it to the 
basic index dictionary.
 