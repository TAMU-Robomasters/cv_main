# # 
# # find the nix opencv
# # 
# venv_folder="./.venv"
# venv_python_folder_name="python3.7"

# function is_command {
#     command -v "$@" >/dev/null 2>&1
# }

# # put local stuff (project and venv) first
# PYTHONPATH="$PWD:$PWD/.venv/lib/$venv_python_folder_name/site-packages:$PYTHONPATH"
# # if on a mac
# if ! [[ "$OSTYPE" == "darwin"* ]]
# then
#     # use python to find and install the apt-get version of opencv
#     # and save the path to opencv inside ./settings/.cache/opencv-python-path.cleanable
#     python3 -c '
# import os
# import time
# with_success = 0
# with_failure = 1
# def has_opencv_lib():
#     files = os.listdir("/usr/lib/python3/dist-packages/")
#     for each in files:
#         if each.startswith("cv2.cpython") and each.endswith(".so"):
#             # save the path of the opencv library
#             os.makedirs("./settings/.cache/")
#             with open("./settings/.cache/opencv-python-path.cleanable", "w") as the_file:
#                 the_file.write(str(each))
#             return True
#     return False

# if has_opencv_lib():
#     exit(with_success)
# else:
#     # if the cv2 doesnt exist, then try to install it
#     print("it appears you dont have the full opencv installed\nI will try to install it with these commands:\n    sudo apt-get update\n    sudo apt-get install -y python3-opencv\n\nNote: your system may need to be restarted (it will mention if it does)\n")
#     time.sleep(3)
#     os.system("sudo apt-get update")  
#     os.system("sudo apt-get install -y python3-opencv")
#     if not has_opencv_lib():
#         print("something went wrong when installing python3-opencv.\nI still cant find the library\nIt should be in /usr/lib/python3/dist-packages/")
#         exit(with_failure)
#     '
    
#     # # if the opencv shared object exists (which it should)
#     # if [[ -f "$(cat "./settings/.cache/opencv-python-path.cleanable")" ]]
#     # then
        
#     # fi
    
#     python_from_nix="$(which -a python | grep '/nix/store' | head -1)"
#     python_from_system="/usr/bin/python3"
#     cv2_shared_object_file="$("$python_from_system" -c "import cv2; print(cv2.__file__)")"
#     if ! [[ -f "$cv2_shared_object_file" ]] 
#     then
#         echo it appears you dont have the full opencv installed
#         echo I will try to install it with these commands:
#         echo "    sudo apt-get update"
#         echo "    sudo apt-get install -y python3-opencv"
#         echo 
#         echo "Note: your system may need to be restarted"
#         echo "(it will mention if it does)"
        
#         sudo apt-get update
#         sudo apt-get install -y python3-opencv
#     fi
    
#     cv2_shared_object_file="$("$python_from_system" -c "import cv2; print(cv2.__file__)")"
#     if ! [[ -f "$cv2_shared_object_file" ]] 
#     then
#         echo "ERROR: it appears the installtion of python3-opencv didn't work"
#     else
#         # if the so object doesn't exist, then copy it
#         if ! [[ -f "$venv_folder/lib/$venv_python_folder_name/site-packages/$(basename "$cv2_shared_object_file")" ]] 
#         then
#             cp "$cv2_shared_object_file" "$venv_folder/lib/$venv_python_folder_name"
#         fi
#     fi
# fi

# # # check if the library dir has been cached
# # name_of_check="libstdcpp_so_6_fix"
# # which_gcc_to_look_for="gcc-8.3.0"
# # location_of_file_cache="./settings/.cache/.$name_of_check.cleanable"
# # # if it hasnt
# # if ! [[ -f "$location_of_file_cache" ]]; then
# #     # make sure the folder exists
# #     mkdir -p "$(dirname "$location_of_file_cache")"
    
# #     # find the first gcc package with the missing libstdc++.so.6
# #     gcc_cpp_lib_path="$(find -L /nix/store/ -name libstdc++.so.6 2>/dev/null | grep -e "$which_gcc_to_look_for-lib/lib" | head -n 1)"
    
    
# #     # save the result to a file (because that^ operation takes awhile)
# #     echo "$gcc_cpp_lib_path" > "$location_of_file_cache"
    
# # fi
# # user
# # # load the path from the cache
# # gcc_cpp_lib_path="$(cat "$location_of_file_cache")"
# # # if the file exists (which it should linux)
# # if [[ -f "$gcc_cpp_lib_path" ]] 
# # then
# #     # get the directory
# #     gcc_lib_path="$(dirname "$gcc_cpp_lib_path")"
    
# #     # update the library variable
# #     export LD_LIBRARY_PATH="$gcc_lib_path:$LD_LIBRARY_PATH"
    
# #     echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
# # fi

# # # also add the path to the libgthread-2.0.so.0
# # ubtunut_gtk_lib="/user/lib/x86_64-linux-gnu"
# # if [[ -d "$ubtunut_gtk_lib" ]]
# # then
# #     export LD_LIBRARY_PATH="$ubtunut_gtk_lib:$LD_LIBRARY_PATH"
# # fi