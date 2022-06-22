from time import time as now

# project imports
from toolbox.globals import path_to, config, print, runtime
import subsystems.model        as model
import subsystems.video_stream as video_stream
import subsystems.aim          as aim
import subsystems.communicate  as communicate
import subsystems.log          as log

# Run detection infinitely
for runtime.frame_number, (runtime.color_image , runtime.depth_image) in enumerate(video_stream.frames()):
    # set frame data
    runtime.initial_time  = now()
    runtime.frame_number  = frame_number
    runtime.screen_center = aim.screen_center(color_image)
    
    # process it
    model.when_frame_arrives()
    aim.when_bounding_boxes_refresh()
    communicate.when_aiming_refreshes()
    log.when_finished_processing_frame()

log.when_iteration_stops()