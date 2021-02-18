if [[ -d "./.venv" ]]
then
    ./settings/commands/.check_pip_modules
else
    echo "cant install python modules because venv wasnt created"
fi