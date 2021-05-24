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

            frames = pipeline.wait_for_frames()     
            # motion_data = frames.as_motion_frame().get_motion_data()
            if accel_frame = frames.first_or_default(RS2_STREAM_ACCEL):
                accel_data = accel_frame.get_motion_data() 
            if gyro_frame = frames.first_or_default(RS2_STREAM_GYRO):
                gyro_data = gyro_frame.get_motion_data()
            if pose_frame = frames.first_or_default(RS2_STREAM_pose):
                pose_data = pose_frame.get_motion_data()
            
            # do whatever with the frames

    finally:
        pipeline.stop()
    return 0