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
    command = <<-HEREDOC.remove_indent
        docker run \
            -it \
            --rm \
            --network=host \
            -v "#{Info.folder}":/project \
            -v /var/run/docker.sock:/var/run/docker.sock \
            -v /usr/local/bin/docker:/usr/local/bin/docker \
            --env PATH="/project/project_bin:${PATH}" \
            -- \
            ubuntu:bionic-20200112
    HEREDOC
    puts command
    exec(command)
    puts ""
    # FIXME
    puts "The command (above) still needs to be converted to windows"
end