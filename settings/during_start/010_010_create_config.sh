config_path="$(cat "$FORNIX_FOLDER/main/info.yaml" | yq '.paths.configuration' | sed -E 's/^"|"$//g')"
# create a subshell
{
    cd "$FORNIX_FOLDER"
    # 
    # init the config if it doesn't exist
    # 
    if ! [ -f "$config_path" ]
    then
        touch "$config_path"
        echo '
# Things at the top of the list will override things at the bottom
# go to ./main/info.yaml look under "configuration" and below the "(default)" and all these options will be listed
- GPU=NONE          # NONE, TENSOR_RT, REGULAR
- BOARD=LAPTOP      # TX2, XAVIER, LAPTOP
- CAMERA=NONE       # ZED, REALSENSE, NONE
- MODE=DEVELOPMENT  # DEVELOPMENT, PRODUCTION
- TEAM=RED          # RED, BLUE
    ' > "$config_path"

    fi
}