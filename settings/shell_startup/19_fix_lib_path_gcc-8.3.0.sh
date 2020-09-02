gcc_cpp_lib_path="$(find -L /nix/store/ -name libstdc++.so.6 | grep -e 'gcc-8.3.0-lib/lib' | head -n 1)"
# if the file exists (which it should linux)
if [[ -f "$gcc_cpp_lib_path" ]] 
then
    # get the lib
    gcc_lib_path="$(dirname "$gcc_cpp_lib_path")"
    # update teh variable
    export LD_LIBRARY_PATH="$gcc_lib_path:$LD_LIBRARY_PATH"
fi
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"