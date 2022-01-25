import time
# relative imports
from toolbox.video_tools import Video
from toolbox.globals import MODE, MACHINE, PATHS, PARAMETERS, print
from toolbox.globals import realsense as rs
from toolbox.globals import zed
import numpy as np

class LiveFeed:
    def __init__(self):
        stream_width = PARAMETERS['aiming']['stream_width']
        stream_height = PARAMETERS['aiming']['stream_height']
        framerate = PARAMETERS['aiming']['stream_framerate']

        self.pipeline = rs.pipeline()                                                               # declares and initializes the pipeline variable
        config = rs.config()                                                                        # declares and initializes the config variable for the pipeline
        config.enable_stream(rs.stream.depth, stream_width, stream_height, rs.format.z16, framerate)  # this starts the depth stream and sets the size and format
        config.enable_stream(rs.stream.color, stream_width, stream_height, rs.format.bgr8, framerate) # this starts the color stream and set the size and format
        # config.enable_stream(rs.stream.accel,rs.format.motion_xyz32f,250)
        # config.enable_stream(rs.stream.gyro,rs.format.motion_xyz32f,200)
        # config.enable_stream(rs.stream.pose,rs.format.motion_xyz32f,200)
        self.profile = self.pipeline.start(config)
        
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
    
    def get_profile(self):
        return self.profile;

    
    def __del__(self):
        print("Closing Realsense Pipeline")
        self.pipeline.stop()

class LiveFeedZed:
    def __init__(self):
        self.camera = zed.Camera()
        # TODO - make these params dependent on config. is the format something we need to worry about? (int8 vs ...)
        init_params = zed.InitParameters()
        init_params.camera_resolution = zed.RESOLUTION.HD720
        init_params.camera_fps = PARAMETERS['aiming']['stream_framerate']
        init_params.depth_mode = zed.DEPTH_MODE.PERFORMANCE
        init_params.coordinate_units = zed.UNIT.METER
        # TODO - customize runtime params with config
        self.runtime_parameters = zed.RuntimeParameters()

        err = self.camera.open(init_params)
        while err != zed.ERROR_CODE.SUCCESS:
            print('VideoStream: Failed to open ZED camera! Retrying...')
            err = self.camera.open(init_params)
        
        # Create an RGBA sl.Mat object with int8
        self.image_zed = zed.Mat(self.camera.get_camera_information().camera_resolution.width, self.camera.get_camera_information().camera_resolution.height, zed.MAT_TYPE.U8_C4)
        # Create a sl.Mat with float type (32-bit)
        self.depth_zed = zed.Mat(self.camera.get_camera_information().camera_resolution.width, self.camera.get_camera_information().camera_resolution.height, zed.MAT_TYPE.F32_C1)
        
    def get_live_video_frame(self):
        # retry after failure
        while True:
            if self.camera.grab(self.runtime_parameters) == zed.ERROR_CODE.SUCCESS:
                self.camera.retrieve_image(self.image_zed, zed.VIEW.LEFT)
                self.camera.retrieve_measure(self.depth_zed, zed.MEASURE.DEPTH)
                # Convert images to ocv format
                color_image = self.image_zed.get_data()
                depth_image = self.depth_zed.get_data()

                return (color_image, depth_image)
            if MODE == 'development':
                print("VideoStream: unable to retrieve frame.")
                print('(retrying)')
    
    def __del__(self):
        print("Closing ZED camera")
        self.camera.close()

if PARAMETERS['videostream']['hardware']['camera'] == 'ZED':
    LiveFeed = LiveFeedZed
