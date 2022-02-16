import time
# relative imports
from toolbox.video_tools import Video
from toolbox.globals import MACHINE, PATHS, PARAMETERS, print
from toolbox.globals import realsense as rs
import numpy as np
import pyzed.sl as sl

class LiveFeed:
    def __init__(self):
        stream_width = PARAMETERS['aiming']['stream_width']
        stream_height = PARAMETERS['aiming']['stream_height']
        framerate = PARAMETERS['aiming']['stream_framerate']


        # Create a ZED camera object
        self.zed = sl.Camera()

        # Set configuration parameters
        init = sl.InitParameters()
        init.camera_resolution = sl.RESOLUTION.HD1080
        init.camera_fps = 30
        init.depth_mode = sl.DEPTH_MODE.PERFORMANCE
        init.coordinate_units = sl.UNIT.MILLIMETER

        # Open the camera
        err = self.zed.open(init)
        if err != sl.ERROR_CODE.SUCCESS :
            print(repr(err))
            self.zed.close()
            exit(1)

        # Set runtime parameters after opening the camera
        runtime = sl.RuntimeParameters()
        runtime.sensing_mode = sl.SENSING_MODE.STANDARD
        
    def get_camera(self):
        return self.zed
    
    def __del__(self):
        print("Closing Realsense Pipeline")
        self.pipeline.stop()
    