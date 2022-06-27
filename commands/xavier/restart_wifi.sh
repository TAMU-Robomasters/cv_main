
    while true
    do
        sleep 30
        # check if there is internet via ping test
        if ! [ "`ping -c 1 google.com`" ]; then #if ping exits nonzero...
            sudo service networking restart #restart the whole thing
            echo Networking service restarted due to no ping response from google.com
        fi
    done

        
         