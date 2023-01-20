import torch
import time
from quik_config import find_and_load
from super_map import LazyDict
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

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
config = info.config         # the resulting dictionary for all the selected options
# a dictionary of paths relative to the root_path
path_to = info.path_to
# same dictionary of paths, but made absolute
absolute_path_to = info.absolute_path_to

# shared global data
runtime = LazyDict()

#
# print (so we can disable it in production for performance)
#
original_print = print
if config.log.disable_print:
    def print(*args, **kwargs): pass  # do nothing
else:
    def print(*args, **kwargs):
        # force writing to a file (slows down program but makes log files update immediately)
        kwargs["flush"] = True
        original_print(*args, **kwargs)


def time_synchronized():
    # pytorch-accurate time
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    return time.time()
