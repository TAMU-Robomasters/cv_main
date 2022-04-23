from quik_config import find_and_load

# load the info.yaml
info = find_and_load(
    "main/info.yaml",
    cd_to_filepath=True,
    parse_args=True,
    defaults_for_local_data=[
        "GPU=NONE",
        "BOARD=LAPTOP",
        "CAMERA=NONE",
        "MODE=DEVELOPMENT",
        "TEAM=RED",
    ],
)

# create all of these for exporting
config                = info.config         # the resulting dictionary for all the selected options
path_to               = info.path_to               # a dictionary of paths relative to the root_path
absolute_path_to      = info.absolute_path_to      # same dictionary of paths, but made absolute
secrets               = info.secrets               # same dictionary of paths, but made absolute
project               = info.project               # the dictionary to everything inside (project)
root_path             = info.root_path             # parent folder of the .yaml file
selected_profiles     = info.selected_profiles     # the dictionary of the local config-choices files
profile_names         = info.profile_names         # the dictionary of all possible options
as_dict               = info.as_dict               # the dictionary to the whole file (info.yaml)

# 
# print (so we can disable it in production for performance)
# 
original_print = print
def print(*args,**kwargs):
    if config.mode == "development":
        original_print(*args,**kwargs)

# 
# set port permissions
# 
if config.hardware.board == "xavier":
    import subprocess
    print("giving myself access to the communication port...")
    subprocess.run(["sudo", "chmod", "777", "/dev/ttyTHS0"])


print(config)