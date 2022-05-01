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
import subsystems.model        as model
import subsystems.aim          as aim
import subsystems.communicate  as communicate
import subsystems.log          as log
import subsystems.video_stream as video_stream

# Run detection infinitely
for frame_number, (color_image, depth_image) in enumerate(video_stream.frames()):
    # set frame data
    runtime.initial_time  = time.time()
    runtime.frame_number  = frame_number
    runtime.color_image   = color_image
    runtime.depth_image   = depth_image
    runtime.screen_center = aim.screen_center(color_image)
    
    # process it
    model.when_frame_arrives()
    aim.when_bounding_boxes_refresh()
    communicate.when_aiming_refreshes()
    log.when_finished_processing_frame()