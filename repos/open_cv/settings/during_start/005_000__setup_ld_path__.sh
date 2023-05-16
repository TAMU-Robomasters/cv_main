# attempt to link cuda if it exists
if [ -f "/usr/local/cuda/bin/nvcc" ]
then
    export PATH="$PATH:/usr/local/cuda/bin/"
fi

if [ "$OSTYPE" = "linux-gnu" ] 
then
    export LD_LIBRARY_PATH="$("$__FORNIX_NIX_COMMANDS/lib_path_for" "cc"):$LD_LIBRARY_PATH"
fi