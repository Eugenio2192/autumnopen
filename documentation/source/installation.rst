Installation
============

To install, clone the repository  in your computer by using git or downloading it. It is recommended that an environment virtual environment is created for the project,either from conda or any other package manager.  Once you have it in your system install the dependencies using conda doing:

.. prompt:: bash

        conda install yaml pandas geopandas cartopy seaborn scikit-learn statsmodels scipy dash plotly -c conda-forge

Or with pip using: 

.. prompt:: bash

        pip install yaml pandas geopandas cartopy seaborn scikit-learn statsmodels scipy dash plotly
    
Once the dependencies are installed, the background operations have to be fulfilled, to do so, import the api using:

.. code-block:: python
        
        from src. api import *

And then, with python, running::

	>>>initialize()
	2020-11-30 14:02:20 INFO     Starting harmonization
	2020-11-30 14:02:23 INFO     Calculating cost values
	2020-11-30 14:02:23 INFO     Creating power plant input file
	2020-11-30 14:02:29 INFO     Creating power plant cost potential file
	2020-11-30 14:02:36 INFO     Creating iron and steel cost potential file
	2020-11-30 14:02:36 INFO     Creating cement cost potential file	

Then you should be good to go.        

