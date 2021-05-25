import pyrealsense2 as rs
import numpy as np
import cv2

pipeline = rs.pipeline()                                            # declares and initializes the pipeline variable
config = rs.config()                                                # declares and initializes the config variable for the pipeline
config.enable_stream(rs.stream.accel,rs.format.motion_xyz32f,200)
config.enable_stream(rs.stream.gyro,rs.format.motion_xyz32f,200)
profile = pipeline.start(config)

def DistanceInBox(bbox):
    try:

        last_ts = None
        euler_vector = np.array([[0], [0], [0]])    # subject to change -- what is the initial roll/pitch/yaw of the turret?
        
        while True: 

            frames = pipeline.wait_for_frames()     # frames is composite_frame

            # get frame for acceleration and gyroscope (accel_frame and gyro_frame are type frame)
            accel_frame = frames.first_or_default(rs.stream.accel)
            gyro_frame = frames.first_or_default(rs.stream.gyro)

            if last_ts is None:
                last_ts = gyro_frame.get_timestamp() / 1000
                continue


            if accel_frame is not None:
                accel_data = accel_frame.as_motion_frame().get_motion_data() 
            if gyro_frame is not None:
                gyro_data = gyro_frame.as_motion_frame().get_motion_data()

            accel_vector = np.array([[accel_data.x],
                                     [accel_data.y],
                                     [accel_data.z]])
            gryo_vector = np.array([[gyro_data.x],
                                    [gyro_data.y],
                                    [gyro_data.z]])
            epsilon = 0.98

            # time is measured in in milliseconds
            ts = gyro_frame.get_timestamp() / 1000
            delta_t = ts - last_ts
            last_ts = ts

            accel_rot_vector = np.array([[np.arctan2(accel_data.y, accel_data.x)],
                                         [np.arctan2(accel_data.z, np.sqrt((accel_data.x)**2 + (accel_data.y)**2))]
                                         [0]])
            
            euler_vector += epsilon * delta_t * gryo_vector + (1 - epsilon) * accel_rot_vector
            
            # do whatever with the frames
    finally:
        pipeline.stop()
    return 0
