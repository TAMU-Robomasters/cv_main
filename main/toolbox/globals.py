import os

import numpy as np
from super_map import Map, LazyDict
from walk_up import walk_up_until
import ez_yaml
from dict_recursive_update import recursive_update
from quik_config import find_and_load

# relative imports
from toolbox.file_system_tools import FS

# load the info.yaml
data = find_and_load(
    "main/info.yaml",
    default_options=[
        "GPU=NONE",
        "BOARD=LAPTOP",
        "CAMERA=NONE",
        "MODE=DEVELOPMENT",
        "TEAM=RED",
    ],
    go_to_root=False,
)

# create all of these for exporting
config                = data.config                # the resulting dictionary for all the selected options
info                  = data.info                  # the dictionary to the whole file (info.yaml)
project               = data.project               # the dictionary to everything inside (project)
root_path             = data.root_path             # parent folder of the .yaml file
path_to               = data.path_to               # a dictionary of paths relative to the root_path
absolute_path_to      = data.absolute_path_to      # same dictionary of paths, but made absolute
configuration         = data.configuration         # the dictionary of the local config-choices files
configuration_options = data.configuration_options # the dictionary of all possible options

# 
# print
# 
original_print = print
def print(*args,**kwargs):
    if config.mode == "development":
        original_print(*args,**kwargs)