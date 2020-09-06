# 
# add this project folder to the python path
# 
if [ -z "$PYTHONPATH" ]
then
    # pythonpath is empty, just set to to PWD
    PYTHONPATH="$PWD"
      echo "\$var is empty"
else
    # otherwise put it after the other modules
    PYTHONPATH="$PYTHONPATH:$PWD"
fi