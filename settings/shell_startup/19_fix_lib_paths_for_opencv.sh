# 
# libstdc++.so.6 fix
# 
name_of_check="libstdcpp_so_6_fix"
which_gcc_to_look_for="gcc-8.3.0-lib"
location_of_file_cache="./settings/.cache/.$name_of_check.cleanable"
# if it hasnt cached it
if ! [[ -f "$location_of_file_cache" ]]; then
    # make sure the folder exists
    mkdir -p "$(dirname "$location_of_file_cache")"
    
    # find the first gcc package with the missing libstdc++.so.6
    lib_path="$(find -L /nix/store/ -name libstdc++.so.6 2>/dev/null | grep -e "$which_gcc_to_look_for/lib" | head -n 1)"
    
    
    # save the result to a file (because that^ operation takes awhile)
    echo "$lib_path" > "$location_of_file_cache"
    
fi
# load the path from the cache
lib_path="$(cat "$location_of_file_cache")"
# if the file exists (which it should linux)
if [[ -f "$lib_path" ]] 
then
    # get the directory
    lib_dir="$(dirname "$lib_path")"
    
    # update the library variable
    export LD_LIBRARY_PATH="$lib_dir:$LD_LIBRARY_PATH"
    
    echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
fi


# 
# libSM fix
# 
name_of_check="libSM"
which_gcc_to_look_for="libSM-1.2.3"
location_of_file_cache="./settings/.cache/.$name_of_check.cleanable"
# if it hasnt cached it
if ! [[ -f "$location_of_file_cache" ]]; then
    # make sure the folder exists
    mkdir -p "$(dirname "$location_of_file_cache")"
    
    # find the first package with the missing lib
    lib_path="$(find -L /nix/store/ -name libSM.so.6 2>/dev/null | grep -e "$which_gcc_to_look_for/lib" | head -n 1)"
    
    # save the result to a file (because that^ operation takes awhile)
    echo "$lib_path" > "$location_of_file_cache"
    
fi
# load the path from the cache
lib_path="$(cat "$location_of_file_cache")"
# if the file exists (which it should linux)
if [[ -f "$lib_path" ]] 
then
    # get the directory
    lib_dir="$(dirname "$lib_path")"
    
    # update the library variable
    export LD_LIBRARY_PATH="$lib_dir:$LD_LIBRARY_PATH"
    
fi

# 
# libgthread-2.0.so.0 fix
# 
ubtunut_gtk_lib="/usr/lib/x86_64-linux-gnu"
if [[ -d "$ubtunut_gtk_lib" ]]
then
    export LD_LIBRARY_PATH="$ubtunut_gtk_lib:$LD_LIBRARY_PATH"
fi

echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"