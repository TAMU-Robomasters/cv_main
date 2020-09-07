# 
# if on a mac
# 
if [[ "$OSTYPE" == "darwin"* ]]
then
    # use the virual enviornment
    ls .venv &>/dev/null || python -m venv .venv
    source .venv/bin/activate
# 
# linux
# 
else
    # opencv breaks inside venv for linux, and I'm not sure how to fix it
    # so on linux we don't use venv even though thats more likely to cause problems down the road
    
    # 
    # pip3 check
    #
    pip_from_system="/usr/bin/pip3"
    if ! [[ -f "$pip_from_system" ]]
    then
        echo 
        echo "It appears you don't have pip3 (I looked at /usr/bin/pip3)"
        echo "I'll try to install python for you using this commands:"
        echo "    sudo apt-get update"
        echo "    sudo apt-get install -y python3-pip"
        echo 
        
        sudo apt-get update
        sudo apt-get install -y python3-pip
    fi
    # check again for pip3 encase the installtion went bad
    if ! [[ -f "$pip_from_system" ]]
    then
        echo "it looks like pip3 still isn't installed."
        echo "I'll let the rest of the project load but it will likely be broken"
    else
        
        # 
        # python3 check
        # 
        # make sure python3 is installed
        python_from_system="/usr/bin/python3"
        if ! [[ -f "$python_from_system" ]]
        then
            echo 
            echo "It appears you don't have python3 (I looked at /usr/bin/python3)"
            echo "I'll try to install python for you using this commands:"
            echo "    sudo apt-get update"
            echo "    sudo apt-get install -y python3"
            echo 
            
            sudo apt-get update
            sudo apt-get install -y python3
        fi
        # check again for python3 encase the installtion went bad
        if ! [[ -f "$python_from_system" ]]
        then
            echo "it looks like python3 still isn't installed."
            echo "I'll let the rest of the project load but it will likely be broken"
        # if python3 exists
        else
        
            # 
            # opencv check
            # 
            # look for the opencv installation
            cv2_shared_object_file="$("$python_from_system" -c "import cv2; print(cv2.__file__)")"
            if ! [[ -f "$cv2_shared_object_file" ]] 
            then
                echo it appears you dont have the full opencv installed
                echo I will try to install it with these commands:
                echo "    sudo apt-get update"
                echo "    sudo apt-get install -y python3-opencv"
                echo 
                echo "Note: your system may need to be restarted"
                echo "(it will mention if it does)"
                
                sudo apt-get update
                sudo apt-get install -y python3-opencv
            fi
        fi
    fi
fi