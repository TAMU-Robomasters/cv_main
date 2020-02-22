require 'atk_toolbox'
require_relative Info.paths["ruby_tools"] # corrisponds to the "(path)" inside info.yaml file

# keep a log of the current abs path of your project
# this is needed for starting up docker instances
project_path = FS.absolute_path($info.folder)
FS.write(project_path, to: $paths["project_dir_file"])

# 
# build all the docker images
# 
for each in FS.list_files($paths["dockerfiles"]).select{|each|!(each =~ /\.dockerignore$/)}
    puts ""
    puts "Building docker file: #{FS.basename(each).to_s.green}"
    puts ""
    *folders, name, ext = FS.path_pieces(each)
    # build each dockerfile
    LocalDocker.new(name).build(
        $paths["dockerfiles"]/"#{name}.DockerFile",
        files_to_include:[
            "project_bin",
            *FS.list_files
        ],
    )
    if not $?.success?
        exit
    end
end

puts "#".green
puts "# setup complete".green
puts "#".green