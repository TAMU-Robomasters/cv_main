require 'atk_toolbox'
require_relative Info.paths["ruby_tools"] # corrisponds to the "(path)" inside info.yaml file

# 
# local setup
# 
if Console.yes?("would you like perform a local setup? (the alternative is docker)")
    # 
    # check for python
    # 
    if !Console.has_command?("python3") || !Console.has_command?("pip3")
        puts "You're going to need python3 and pip3"
        if OS.is?(:mac)
            if Console.yes?("Would you like me to install them for you?")
                system("brew install python@3 2>/dev/null")
                system("brew link --overwrite python@3 2>/dev/null")
            end
        else
            puts "Please install them and then re-run this command"
            puts "also:"
            puts "    make sure there is a #{"python3".color_as :code} and #{"pip3".color_as :code} alias"
            puts "    don't only have the #{"python".color_as :code} command point to python3"
            exit 1
        end
    end
    
    puts "# "
    puts "# "
    puts "# installing pip packages"
    puts "# "
    puts "# "
    error = !system("pip3 install -r requirements.txt")
    error &&= !system("pip3 install --ignore-installed PyYAML==5.1.2")
    if !error && OS.is?("mac")
        error &&= !system("brew install opencv")
    end
    # uninstall opencv to avoid the "cannot import TrackerMOSSE_create from cv2.cv2"
    error &&= !system("pip3 uninstall opencv-python") 
    
    # report errors
    if error
        puts ""
        puts "it appears something went wrong while installing the pip packages"
        puts "thats all this script knows, please rerun once when you're able to resolve it"
        exit 1
    end
end


# 
# 
# docker setup
# 
# 
if Console.yes?("\n\n\nwould you like setup docker?")
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
end
puts "#".green
puts "# setup complete".green
puts "#".green