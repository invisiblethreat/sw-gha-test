"""Load YAML config as a Singleton."""

from typing import Dict

CONFIG_PATH = "config.yml"

def __get_module_path() -> str:
    import os
    basepath = os.path.dirname(os.path.realpath(__file__))
    return basepath

def __load_config(filename: str) -> Dict:
    import yaml
    config_full_path = "%s/%s" % (__get_module_path(), filename)
    with open(config_full_path, 'r') as stream:
        return yaml.load(stream, Loader=yaml.FullLoader)

cfg = __load_config(CONFIG_PATH)
globals().update(cfg)
