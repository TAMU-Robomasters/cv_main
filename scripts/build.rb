require 'atk_toolbox'
require_relative Info.paths["ruby_tools"] # corrisponds to the "(path)" inside info.yaml file

puts "This can take awhile depending on your hardware and internet (probably well over >10min)"
LocalDocker.new(Console.args[0]).build(
    $paths["dockerfiles"]/"#{Console.args[0]}.DockerFile",
    files_to_include:[
        "project_bin",
        *FS.list_files
    ],
)
puts "Task complete".green