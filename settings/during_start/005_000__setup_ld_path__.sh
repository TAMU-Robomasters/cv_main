# attempt to link cuda if it exists
if [ -f "/usr/local/cuda/bin/nvcc" ]
then
    export PATH="$PATH:/usr/local/cuda/bin/"
fi