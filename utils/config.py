import yaml
import os


PATH = os.path.dirname(__file__)
CONFIG_FILE = "{}/../_config.yml".format(PATH)

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return yaml.load(f, Loader=yaml.FullLoader)
