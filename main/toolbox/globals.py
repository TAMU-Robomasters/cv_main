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
#     MACHINE
#     MODE
#     INFO
#     MODEL_LABELS
#     MODEL_COLORS


# 
# load the info.yaml
# 
INFO = yaml.unsafe_load(FS.read(FS.join(FS.dirname(__file__),'..','info.yaml')))

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

# 
# MODE and MACHINE
# 
import os
# laptop or tx2 (default laptop), and it to be overridden by the 'PROJECT_ENVIRONMENT' environment variable
MACHINE = os.environ.get('PROJECT_ENVIRONMENT',"xavier")
# development or production (default to development), and allow for it to be overridden as well
MODE = os.environ.get('PROJECT_MODE',"development")

# 
# PARAMETERS
# 
PARAMETERS = INFO["default_parameters"]
ENVIRONMENT_PARAMETERS = INFO["environment_parameters"][MACHINE]
from dict_recursive_update import recursive_update
PARAMETERS = recursive_update(PARAMETERS, ENVIRONMENT_PARAMETERS)

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

# 
# print
# 
original_print = print
def print(*args,**kwargs):
    global MODE
    if MODE == "development":
        # bundle up prints
        if print.collect_prints:
            for each in args:
                print.collection.append(each)
        # release bundle
        else:
            args = list(args)
            args += print.collection
            print.collection = []
            return original_print(*args,**kwargs)
    # if not in development (e.g. production) don't print anything
print.collection = []
print.collect_prints = False

# 
# dynamic imports
# 
if MACHINE == "laptop":
    print("MACHINE IS LAPTOP")
    realsense = None
    zed = None
else:
    import pyrealsense2.pyrealsense2 as realsense
    if PARAMETERS['videostream']['hardware']['camera'] == 'ZED':
        import pyzed.sl as zed
        if MODE == "development":
            print('Using camera: zed')
            print('Overriding aiming config vals with zed presets')
        # FIXME - better to use overriding feature already present in environment parameters?
        # Would require a CAMERA_TYPE environment variable.
        PARAMETERS['aiming']['stream_width'] = PARAMETERS['aiming']['zed_stream_width']
        PARAMETERS['aiming']['stream_height'] = PARAMETERS['aiming']['zed_stream_height']
        PARAMETERS['aiming']['stream_framerate'] = PARAMETERS['aiming']['zed_stream_framerate']
        PARAMETERS['aiming']['grid_size'] = PARAMETERS['aiming']['zed_grid_size']
        PARAMETERS['aiming']['horizontal_fov'] = PARAMETERS['aiming']['zed_horizontal_fov']
        PARAMETERS['aiming']['vertical_fov'] = PARAMETERS['aiming']['zed_vertical_fov']
    else:
        import pyrealsense2.pyrealsense2 as realsense
        if MODE == "development":
            print('Using camera: realsense')
