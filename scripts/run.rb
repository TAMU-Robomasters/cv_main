require 'atk_toolbox'
require_relative Info.paths["ruby_tools"] # corrisponds to the "(path)" inside info.yaml file

first_argument, *other_arguments = Console.args

# give yourself permission to execute the executable
if OS.is?(:unix)
    system("chmod", "u+x", $paths['project_bin']/first_argument)
end

if OS.is?(:linux)
    exec("sudo", $paths['project_bin']/first_argument, *other_arguments )
elsif OS.is?(:mac)
    exec($paths['project_bin']/first_argument, *other_arguments )
else
    command = [
        'docker',
        'run',
        '-it',
        '--rm',
        '--network=host',
        '-v', "#{Info.folder}:/project",
        '--workdir', '/project/ ',
        '-v', '//var/run/docker.sock:/var/run/docker.sock',
        '-v','/usr/local/bin/docker:/usr/local/bin/docker',
        '--',
        LocalDocker.new("main").image_name,
        *Console.args
    ]
    # helpful sources: https://stackoverflow.com/questions/36765138/bind-to-docker-socket-on-windows
    puts command.join(" ")
    # TODO: test this on windows
    exec(*command)
end