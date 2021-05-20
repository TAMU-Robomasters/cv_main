if [[ -d "./.venv" ]]
then
    "$PROJECTR_COMMANDS_FOLDER/.check_pip_modules"
else
    echo "cant install python modules because venv wasnt created"
fi