from toolbox.globals import config, print, runtime

# 
# pick which one
# 
if config.model.which_model == "yolo_v5":
    from main.subsystems.modeling.yolo_v5 import when_frame_arrives
elif config.model.which_model == "yolo_v4":
    from main.subsystems.modeling.yolo_v4 import when_frame_arrives