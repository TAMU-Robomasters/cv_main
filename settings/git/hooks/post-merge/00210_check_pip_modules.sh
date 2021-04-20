# if PROJECTR_FOLDER is not set, then assume the current folder
if [[ -z "$PROJECTR_FOLDER" ]]
then
    "$PROJECTR_FOLDER/settings/commands/.check_pip_modules"
fi