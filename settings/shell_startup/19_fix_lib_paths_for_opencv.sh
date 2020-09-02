# # find all the shared objects
# shared_objects_file="./settings/.cache/.shared_objects.cleanable"
# # cache them
# if ! [[ -f "$shared_objects_file" ]] 
# then
#     echo "Finding the shared objects"
#     mkdir -p "$(dirname "$shared_objects_file")"
#     find -L /nix/store/ -name "libstdc++.so.6" 2>/dev/null | head -1 >> $shared_objects_file
#     find -L /nix/store/ -name "libSM.so.6" 2>/dev/null | head -1 >> $shared_objects_file
#     find -L /nix/store/ -name "libICE.so.6" 2>/dev/null | head -1 >> $shared_objects_file
# fi
# # iterate through them
# while IFS= read -r line; do
#     # dump all of them in the LD_LIBRARY_PATH
#     export LD_LIBRARY_PATH="$(dirname "$line"):$LD_LIBRARY_PATH"
# done <<< "$(cat "$shared_objects_file")"


# # 
# # libgthread-2.0.so.0 fix
# # 
# ubtunut_gtk_lib="/usr/lib/x86_64-linux-gnu"
# if [[ -d "$ubtunut_gtk_lib" ]]
# then
#     export LD_LIBRARY_PATH="$ubtunut_gtk_lib:$LD_LIBRARY_PATH"
# fi

# echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"