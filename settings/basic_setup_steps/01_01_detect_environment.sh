export PROJECT_ENVIRONMENT="laptop"

__temp_var_linux_hardware_fingerprint="$(lshw -short 2>/dev/null | grep -v network | md5sum)"

# 
# nvidia TX2
# 
if [[ "$__temp_var_linux_hardware_fingerprint" = "a71c50fc183d536f928235a80336c3e6  -" ]]
then
    export PROJECT_ENVIRONMENT="tx2"

# 
# xavier 
# 
elif [[ "$__temp_var_linux_hardware_fingerprint" = "1881eef7a7b4dd13d5af217686774763  -" ]] 
then
    export PROJECT_ENVIRONMENT="xavier"
fi

# NOTE: you can add your own computer here if you want, just make sure to have a good fingerprint method