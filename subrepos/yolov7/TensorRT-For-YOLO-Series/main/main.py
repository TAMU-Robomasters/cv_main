from toolbox.globals import config, print, runtime

import subsystems.video_stream as video_stream
import subsystems.model        as model
import subsystems.aim          as aim
import subsystems.communicate  as communicate
import subsystems.log          as log

# Run detection infinitely
for runtime.frame_number, runtime.color_image , runtime.depth_image in video_stream.frames():
    model.when_frame_arrives()
    aim.when_bounding_boxes_refresh()
    communicate.when_aiming_refreshes()
    log.when_finished_processing_frame()

log.when_iteration_stops()