require 'atk_toolbox'
require_relative Info.paths["ruby_tools"] # corrisponds to the "(path)" inside info.yaml file

first_argument, *other_arguments = Console.args

# give yourself permission to execute the executable
if OS.is?(:unix)
    system("chmod", "u+x", $paths['project_bin']/first_argument)
end

if OS.is?(:linux)
    exec("sudo", $paths['project_bin']/first_argument, *other_arguments )
else
    exec($paths['project_bin']/first_argument, *other_arguments )
end