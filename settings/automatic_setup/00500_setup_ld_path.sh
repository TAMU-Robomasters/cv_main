# add the path to the c lib, which prevents the libstdc++.so.6 errors 
export LD_LIBRARY_PATH="$("$__PROJECTR_NIX_COMMANDS/lib_path_for" "cc"):$LD_LIBRARY_PATH"

# these can probably be removed (was saving encase libglvnd is enabled inside nix.toml file)
# export LD_LIBRARY_PATH="$("$PROJECTR_COMMANDS_FOLDER/tools/nix/lib_path_for" libglvnd):$LD_LIBRARY_PATH"
# export LD_LIBRARY_PATH="$("$PROJECTR_COMMANDS_FOLDER/tools/nix/lib_path_for" glib):$LD_LIBRARY_PATH"