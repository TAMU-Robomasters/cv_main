# find the path to the c lib
# FIXME: this needs better escaping of the $PROJECTR_FOLDER
output="$(
    nix-instantiate --eval -E '"${
        (rec {
            packageJson = builtins.fromJSON (builtins.readFile "'"$PROJECTR_FOLDER/settings/requirements/simple_nix.json"'");
            mainRepo = builtins.fetchTarball {url="https://github.com/NixOS/nixpkgs/archive/${packageJson.nix.mainRepo}.tar.gz";};
            mainPackages = builtins.import mainRepo {
                config = packageJson.nix.config;
            };
            path = mainPackages.stdenv.cc.cc.lib;
        }).path
    }"' | sed -E 's/^"|"$//g'
)"
# prevents the libstdc++.so.6 errors 
export LD_LIBRARY_PATH="$output/lib/:$LD_LIBRARY_PATH"
export LD_LIBRARY_PATH="$(nix_path_for libglvnd)/lib/:$LD_LIBRARY_PATH"
# export LD_LIBRARY_PATH="$(nix_path_for glib)/lib/:$LD_LIBRARY_PATH"
# TODO: this shouldn't be hardcoded! should be something like the above
export LD_LIBRARY_PATH="/nix/store/9yfbxys7srn3cgx9jsmfcyakwpkwr9fs-glib-2.64.1/lib/:$LD_LIBRARY_PATH"