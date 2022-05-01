# library imports
import cv2
import os
import numpy as np
from itertools import count
import math
import time
import datetime
import collections

# project imports
from toolbox.globals import path_to, config, print, runtime
import subsystems.modeling.modeling_main               as modeling
import subsystems.aiming.aiming_main                   as aiming
import subsystems.embedded_communication.embedded_main as communication
import subsystems.logging.logging_main                 as logging
from subsystems.video_stream.video_stream_main         import video_stream

# Run detection infinitely
for frame_number, (color_image, depth_image) in enumerate(video_stream.frames()):
    # set frame data
    runtime.initial_time  = time.time()
    runtime.frame_number  = frame_number
    runtime.color_image   = color_image
    runtime.depth_image   = depth_image
    runtime.screen_center = aiming.screen_center(color_image)
    
    # process it
    modeling.when_frame_arrives()
    aiming.when_bounding_boxes_refresh()
    communication.when_aiming_refreshes()
    logging.when_finished_processing_frame()