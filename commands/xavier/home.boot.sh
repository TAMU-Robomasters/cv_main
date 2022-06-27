
        # give self access to port (which resets on boot for some reason)
        echo 'trying to give myself access to the port'
        username="xavier3"
        pass="$(cat "/home/$username/.pass")"
        sudo -S usermod -a -G dialout $username <<< "$pass" && echo "gave self access"

        # then run main file
        echo "trying to load zshrc"
        . "/home/$username/.zshrc"
        echo "trying to run cv_main"
        cd "/home/$username/repos/cv_main"
        { sleep 30 && python3 "/home/$username/repos/cv_main/main/main.py" } &
        export PID_OF_MAIN_PY=$!
        
        # { sleep 40 && bash "/home/$username/repos/cv_main/commands/xavier/restart_wifi.sh" &> "/home/$username/.wifi.log" } &
        
        echo "python stuff is running on: $PID_OF_MAIN_PY"
        # see: https://lwn.net/Articles/317814/
        # if file exists
        if [ -f "/proc/$PID_OF_MAIN_PY/oom_adj" ]
        then
            sudo echo '-10' > "/proc/$PID_OF_MAIN_PY/oom_adj"
        fi
        
         