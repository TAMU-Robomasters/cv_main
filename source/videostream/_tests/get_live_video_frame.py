import time
# relative imports
from toolbox.video_tools import Video
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print
import pyrealsense2 as rs
import numpy as np


class liveFeed:
    def __init__(self):
        streamWidth = PARAMETERS['aiming']['stream_width']
        streamHeight = PARAMETERS['aiming']['stream_height']
        framerate = PARAMETERS['aiming']['stream_framerate']

        self.pipeline = rs.pipeline()                                                               # declares and initializes the pipeline variable
        config = rs.config()                                                                        # declares and initializes the config variable for the pipeline
        config.enable_stream(rs.stream.depth, streamWidth, streamHeight, rs.format.z16, framerate)  # this starts the depth stream and sets the size and format
        config.enable_stream(rs.stream.color, streamWidth, streamHeight, rs.format.bgr8, framerate) # this starts the color stream and set the size and format
        self.pipeline.start(config)
        
    def get_live_video_frame(self):
        try:
            frames = self.pipeline.wait_for_frames()     
            if not frames:
                print("CONTINUE LOOP")
                return 0
            return frames
        except:
            print("Unexpected error:", sys.exc_info()[0])
            return None
