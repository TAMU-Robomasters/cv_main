which_gcc_to_look_for="gcc-8.3.0"

# check if the library dir has been cached
name_of_check="libstdcpp_so_6_fix"
location_of_file_cache="./settings/.cache/.$name_of_check.cleanable"
# if it hasnt
if ! [[ -f "$location_of_file_cache" ]]; then
    # make sure the folder exists
    mkdir -p "$(dirname "$location_of_file_cache")"
    
    # find the first gcc package with the missing libstdc++.so.6
    gcc_cpp_lib_path="$(find -L /nix/store/ -name libstdc++.so.6 | grep -e "$which_gcc_to_look_for/lib" | head -n 1)"
    
    echo "heres what I found $(echo "$gcc_cpp_lib_path")"
    
    # save the result to a file (because that^ operation takes awhile)
    echo "$gcc_cpp_lib_path" > "$location_of_file_cache"
    
fi

# load the path from the cache
gcc_cpp_lib_path="$(cat "$location_of_file_cache")"
echo "heres what I found in the file cache $(echo "$gcc_cpp_lib_path")"
# if the file exists (which it should linux)
if [[ -f "$gcc_cpp_lib_path" ]] 
then
    # get the directory
    gcc_lib_path="$(dirname "$gcc_cpp_lib_path")"
    
    # update the library variable
    export LD_LIBRARY_PATH="$gcc_lib_path:$LD_LIBRARY_PATH"
    
    echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
fi