import os

import numpy as np
from super_map import Map, LazyDict
from walk_up import walk_up_until
import ez_yaml
from dict_recursive_update import recursive_update

# relative imports
from toolbox.file_system_tools import FS

# 
# explaination
# 
# this file contains (ideally) constants that can be used in many/most of the tools
# it imports the paths from the info.yaml file so that python knows where everything is
# exports:
#     INFO
#     PATHS
#     config
#     print


# 
# load the info.yaml
# 
INFO = ez_yaml.to_object(
    file_path=walk_up_until("main/info.yaml")
)

# 
# load PATHS
# 
PATHS = INFO["paths"]
# make paths absolute if they're relative
for each_key in PATHS.keys():
    *folders, name, ext = FS.path_pieces(PATHS[each_key])
    # if there are no folders then it must be a relative path (otherwise it would start with the roo "/" folder)
    if len(folders) == 0:
        folders.append(".")
    # if not absolute, then make it absolute
    if folders[0] != "/":
        if folders[0] == '.' or folders[0] == './':
            _, *folders = folders
        PATHS[each_key] = FS.absolute_path(PATHS[each_key])
PATHS = LazyDict(PATHS)

# 
# configuration
# 
# create the default options file if it doesnt exist
if not FS.is_file(PATHS.configuration):
    FS.write(
        to=PATHS.configuration,
        data="""
            # Things at the top of the list will override things at the bottom
            - GPU=NONE
            - BOARD=LAPTOP
            - CAMERA=NONE
            - MODE=DEVELOPMENT
            - TEAM=RED
        """.replace("\n            ","\n"),
    )
selected_options = ez_yaml.to_object(
    file_path=PATHS.configuration,
)
# start off with default
config = INFO["configuration"]["(default)"]
# merge in all the other options
for each_option in reversed(selected_options):
    config = recursive_update(config, INFO["configuration"][each_option])
# create a helper for recursive converting to lazy dict (much more useful than a regular dict)
recursive_lazy_dict = lambda arg: arg if not isinstance(arg, dict) else LazyDict({ key: recursive_lazy_dict(value) for key, value in arg.items() })
config = recursive_lazy_dict(config)

# 
# print
# 
original_print = print
def print(*args,**kwargs):
    if config.mode == "development":
        original_print(*args,**kwargs)