require 'atk_toolbox'
require_relative Info.paths["ruby_tools"] # corrisponds to the "(path)" inside info.yaml file

# add the project to PYTHONPATH
old_python_path = ENV["PYTHONPATH"]
project_path = $paths["project_root"]
source_path = $paths["source_dir"]
ENV["PYTHONPATH"] = "#{old_python_path}:#{project_path}:#{source_path}"
# run the python command
exec("python", *ARGV)