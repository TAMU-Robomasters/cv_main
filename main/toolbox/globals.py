from quik_config import find_and_load
from super_map import LazyDict

# load the info.yaml
info = find_and_load(
    "main/info.yaml",
    cd_to_filepath=True,
    parse_args=True,
    defaults_for_local_data=[
        "GPU=NONE",
        "BOARD=LAPTOP",
        "CAMERA=NONE",
    ],
)

# create all of these for exporting
config                = info.config         # the resulting dictionary for all the selected options
path_to               = info.path_to               # a dictionary of paths relative to the root_path
absolute_path_to      = info.absolute_path_to      # same dictionary of paths, but made absolute

# shared global data
runtime = LazyDict()

# 
# print (so we can disable it in production for performance)
# 
original_print = print
def print(*args,**kwargs):
    kwargs["flush"] = True
    if not config.testing.disable_print:
        original_print(*args,**kwargs)