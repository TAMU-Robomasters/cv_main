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

exclusion = /[^a-z0-9\-._]/
puts "docker"+underscorify(File.absolute_path(__dir__+"/.."), exclusion_regex: exclusion) + ":" + underscorify(ARGV[0], exclusion_regex: exclusion)