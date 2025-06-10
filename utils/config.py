import yaml
import os
from typing import Dict, Any


def load_config() -> Dict[str, Any]:
    PATH = os.path.dirname(__file__)
    CONFIG_FILE = "{}/../_config.yml".format(PATH)

    with open(CONFIG_FILE, "r") as f:
        return yaml.load(f, Loader=yaml.FullLoader)
