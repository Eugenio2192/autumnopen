Customization
=============

In order to tweak the parameters you have two possibilities. Either modifying them directly to the config.yaml file(recommended)
or by using the inbuilt config interaction tool; In this example we set the CostLevel parameter to Range High, the
tree structure shold be the same as the one found in the config file.

.. code-block:: python

	from src.tools.config_loader import Configuration
	config = Configuration.get_instance()	
	config.set_value("range_high", "InputHomogenization", "CostLevel")