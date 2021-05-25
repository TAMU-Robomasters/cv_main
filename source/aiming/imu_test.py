import pyrealsense2 as rs
import numpy as np
import cv2

pipeline = rs.pipeline()                                            # declares and initializes the pipeline variable
config = rs.config()                                                # declares and initializes the config variable for the pipeline
config.enable_stream(rs.stream.accel,rs.format.motion_xyz32f,200)
config.enable_stream(rs.stream.gyro,rs.format.motion_xyz32f,200)
config.enable_stream(rs.stream.pose,rs.format.motion_xyz32f,200)
profile = pipeline.start(config)

def DistanceInBox(bbox):

    try:

        while True: 

            frames = pipeline.wait_for_frames()     # frames is composite_frame

            # get frame for acceleration and gyroscope
            accel_frame = frames.first_or_default(rs.stream.accel)   
            gyro_frame = frames.first_or_default(rs.stream.gyro)

            if accel_frame is not None:
                accel_data = accel_frame.get_motion_data() 
            if gyro_frame is not None:
                gyro_data = gyro_frame.get_motion_data()
            
            # do whatever with the frames
    finally:
        pipeline.stop()
    return 0
