import yaml
import numpy as np
# relative imports
from toolbox.file_system_tools import FS

# 
# explaination
# 
# this file contains (ideally) constants that can be used in many/most of the tools
# it imports the paths from the info.yaml file so that python knows where everything is
# exports:
#     PATHS
#     PARAMETERS
#     ENVIRONMENT
#     MODE
#     INFO
#     MODEL_LABELS
#     MODEL_COLORS


# 
# mode and environment
# 
ENVIRONMENT = "laptop" # laptop, or tx2 
MODE = "development" # development or production
import os
# allow ENVIRONMENT to be overridden by the 'PROJECT_ENVIRONMENT' environment variable
if 'PROJECT_ENVIRONMENT' in os.environ:
    ENVIRONMENT = os.environ['PROJECT_ENVIRONMENT']

# 
# load the info.yaml and some of its data
# 
INFO = yaml.unsafe_load(FS.read(FS.join(FS.dirname(__file__),'..','info.yaml')))
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

PARAMETERS = INFO["parameters"]

# 
# modeling
# 
MODEL_LABELS = open(PATHS["model_labels"]).read().strip().split("\n")
# initialize a list of colors to represent each possible class label
np.random.seed(42)
MODEL_COLORS = np.random.randint(0, 255, size=(len(MODEL_LABELS), 3), dtype="uint8")
# Green in RGB
COLOR_GREEN = (0, 255, 0)
COLOR_YELLOW = (255, 255, 00)