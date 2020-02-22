import yaml
# relative imports
from toolbox.file_system_tools import FS

# 
# explaination
# 
# this file contains constants that can be used in most of the tools
# it imports the paths from the info.yaml file so that python knows where everything is
# exports:
#     INFO
#     PATHS
#     PARAMETERS

# 
# load the info.yaml and some of its data
# 
INFO = yaml.unsafe_load(FS.read(FS.join(FS.dirname(__file__),'..','info.yaml')))
PATHS = INFO["(project)"]["(paths)"]
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

