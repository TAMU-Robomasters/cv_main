require 'atk_toolbox'
require 'nokogiri'
require 'open-uri'
require 'statistics2'

# this gets its value from the info.yaml file
$info = Info.new # load the info.yaml

$paths = $info.paths
path_to_urls = $paths['all_urls']
PARAMETERS = $info['parameters']

class Numeric
    def percent
        return self/100.0
    end
end

def underscorify(string, exclusion_regex:/[^a-z0-9_]/)
    string = string.gsub(/_/, "__")
    string.gsub!(exclusion_regex) do |result|
        output = "_#{result.ord}_"
        # if the lowercase version is allowed, use that instead for readability
        if result =~ /[A-Z]/
            lowercase = result.downcase
            if !(lowercase =~ exclusion_regex)
                output = "_#{lowercase}_"
            end
        end
        output
    end
    return string
end

class LocalDocker
    @@volume = "\"$PWD\":/project"
    @@options = {
        infinite_process: "--entrypoint tail",
        infinite_process_arguments: "-f /dev/null",
        background_process: "-d",
        has_terminal: "-t",
        remove_after_completion: "--rm",
        ability_to_run_other_docker_containers: "-v /var/run/docker.sock:/var/run/docker.sock",
        interactive: "-it",
    }
    
    def initialize(name)
        @name = name
        
        docker_files = FS.list_files($paths["dockerfiles"]).map{|each|FS.basename(each).gsub(/\.[dD]ocker[fF]ile$/,"")}

        # if its not image
        if not docker_files.include?(@name)
            raise <<-HEREDOC.remove_indent
                
                I don't think #{@name} is a dockerfile in the correct location (#{$paths["dockerfiles"]})
                #{docker_files.inspect}
            HEREDOC
        end
    end
    
    def image_name
        # what characters are not allowed (uppercase, spaces, %, ", $, etc)
        exclusion = /[^a-z0-9\-._]/
        return "docker"+underscorify($info.folder, exclusion_regex: exclusion) + ":" + underscorify(@name, exclusion_regex: exclusion)
    end

    def build(docker_file, files_to_include:[])
        # create the docker ignore
        docker_ignore_path = $info.folder/".dockerignore"
        old_docker_ignore = FS.read(docker_ignore_path)
        # the gsubs are for crudely escaping ()'s
        files_to_include = files_to_include.map{|each| "!"+each.gsub(/\(/,"\\(").gsub(/\)/, "\\)")}.join("\n")
        ignore_file_contents = "**/*\n#{files_to_include}"
        FS.write(ignore_file_contents, to: docker_ignore_path )
        
        # try building the image
        success = false
        begin
            where_to_build = Console.as_shell_argument($info.folder)
            
            forward_all_ports = "--network=host"
            which_dockerfile = "--file '#{docker_file}'"
            name_the_image = "-t #{self.image_name}"
            
            options = [
                forward_all_ports,
                which_dockerfile,
                name_the_image,
            ]
            system("docker build #{options.join(" ")} #{where_to_build}")
            success = $?.success?
        ensure
            if old_docker_ignore
                FS.write(old_docker_ignore, to: docker_ignore_path)
            else
                FS.delete(docker_ignore_path)
            end
        end
        return success
    end
    
    def run(arguments:[], interactive: false)
        options = [
            @@options[:ability_to_run_other_docker_containers],
            @@options[:remove_after_completion],
            "-v #{@@volume}", # access_to_current_enviornment
        ]
        options.push(@@options[:interactive]) if interactive
        
        Console.run("docker run #{options.join(" ")} #{self.image_name} "+Console.make_arguments_appendable(arguments))
    end
    
    def edit
        options = [
            @@options[:infinite_process],
            @@options[:background_process],
            @@options[:has_terminal],
            @@options[:remove_after_completion],
            @@options[:ability_to_run_other_docker_containers],
            @@options[:access_to_current_enviornment],
            "-v #{@@volume}", # access_to_current_enviornment
        ]
        
        command = "docker run #{options.join(" ")} #{self.image_name} #{@@options[:infinite_process_arguments]}"
        # start detached run
        container_id = `#{command}`.chomp
        # put user into the already-running process, let the make whatever changes they want
        system("docker exec -it #{container_id} /bin/sh")
        # once they exit that, ask if they want to save those changes
        if Console.yes?("would you like to save those changes?")
            # save those changes to the container
            system "docker commit #{container_id} #{self.image_name}"
        end
        
        # kill the detached process (otherwise it will continue indefinitely)
        system( "docker kill #{container_id}", err:"/dev/null")
        system( "docker stop #{container_id}", err:"/dev/null")
        system( "docker rm #{container_id}", err:"/dev/null")
    end
    
    def remove
        containers = `docker ps | grep #{self.image_name}`.chomp.split("\n")
        # find all the images
        for each_line in containers
            if each_line =~ /^(\w+)\s+#{self.image_name}/
                each_container_id = $1
                puts "killing container: #{each_container_id}"
            else
                next
            end
            # kill/stop/remove
            system("docker", "container", "kill", each_container_id, :err=>"/dev/null")
            system("docker", "container", "stop", each_container_id, :err=>"/dev/null")
            system("docker", "container", "rm", each_container_id, :err=>"/dev/null")
        end
        # remove the image
        system("docker", "image", "rm", self.image_name, :err=>"/dev/null")
    end
    
    def export
        system "docker save #{self.image} > exported-image.tar"
    end
    
    def self.import(tar_file)
        system "docker import #{tar_file}"
    end
end