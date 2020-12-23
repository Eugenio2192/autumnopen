import yaml
from pathlib import Path
import logging

CONFIG_PATH = Path(__file__).parents[2] / "config.yaml"
DEFAULT_CONFIG_PATH = Path(__file__).parents[2] / "default/config.yaml"


class Configuration:
    def __init__(self, path=CONFIG_PATH, **kwargs):
        if Configuration.__instance != None:
            raise Exception("This class is a singleton! once created use global_values = Configuration.get_instance()")
        else:
            Configuration.__instance = self
        self.path = path
        dictionary = self.config_dic()
        for key in dictionary.keys():
            setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])

    __instance = None

    def __getitem__(self, item):
        return getattr(self, item)

    def config_dic(self):
        config = self.load_yaml(self.path)
        config.update({"IO": self.create_path_dictionary(config)})
        return config

    def set_value(self, value, *levels):
        if len(levels) <= 1:
            logging.info("Root levels are protected, please insert another level")
        self.__set_value(self.__dict__, value, *levels)
        return

    @classmethod
    def __set_value(cls, dic, value, *levels):
        levels =list(levels)
        local_config = dic.get(levels[0])
        if len(levels)==1:
            dic[levels[0]] = value
            return
        else:
            levels.pop(0)
            cls.__set_value(local_config, value, *levels)


    @staticmethod
    def load_yaml(filepath):
        """loads config.yaml"""
        with open(filepath, "r") as file:
            data = yaml.full_load(file)
        return data

    @staticmethod
    def create_path_dictionary(raw):
        parent = Path(__file__).parents[2]
        raw = raw["IO"]
        paths = {k: parent / "Data" / v for k, v in raw.items()}
        paths["figures_path"] = parent / raw["figures_path"]
        return paths

    @classmethod
    def reset_defaults(cls, **kwargs):
        default = cls.load_yaml(DEFAULT_CONFIG_PATH)
        with open(CONFIG_PATH, "w") as file:
            yaml.dump(default, file)
        logging.info("The configuration values have been reset")

    @staticmethod
    def get_instance():
        """ Static access method. """
        if Configuration.__instance == None:
            Configuration()
        return Configuration.__instance


#config = Configuration(CONFIG_PATH)
