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
        
        # "global variables"
        last_ts_accel = None
        last_ts_gyro = None
        euler = np.array([[0], [0], [0]])    # subject to change -- what is the initial roll/pitch/yaw of the turret?
        velocity = np.array([[0], [0], [0]])

        while True: 
            # ~~~~~~~~~~~~~~~~~~~~~~~~~ COLLECT IMU SENSOR INPUT ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
            
            # get frame for acceleration and gyroscope
            frames = pipeline.wait_for_frames()
            accel_frame = frames.first_or_default(rs.stream.accel)
            gyro_frame = frames.first_or_default(rs.stream.gyro)

            if accel_frame is not None or gyro_frame is not None:
                if accel_frame is not None:
                    accel_data = accel_frame.as_motion_frame().get_motion_data() 
                if gyro_frame is not None:
                    gyro_data = gyro_frame.as_motion_frame().get_motion_data()
                continue

            if last_ts_accel is None or last_ts_gyro is None:
                if last_ts_accel is None:
                    last_ts_accel = accel_frame.get_timestamp() / 1000
                if last_ts_gyro is None:
                    last_ts_gyro = gyro_frame.get_timestamp() / 1000
                continue
            # ^^ this control flow works... is there a better (more time efficient) way?

            # parse data into vectors
            accel_vector = np.array([[accel_data.x],
                                     [accel_data.y],
                                     [accel_data.z]])
            gryo_vector = np.array([[gyro_data.x],
                                    [gyro_data.y],
                                    [gyro_data.z]])
            
            # ~~~~~~~~~~~~~~~~~~~~~~~~~ CALCULATE IMU ORIENTATION ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
            
            epsilon = 0.98  # weighted average between gyro and accel data, more emphasis on gyro

            ts_gyro = gyro_frame.get_timestamp() / 1000     # time is measured in in milliseconds
            delta_t_gyro = ts_gyro - last_ts_gyro
            last_ts_gyro = ts_gyro

            # rotation measured from accelerometers
            accel_rot_vector = np.array([[np.arctan2(accel_data.y, accel_data.x)],
                                         [np.arctan2(accel_data.z, np.sqrt((accel_data.x)**2 + (accel_data.y)**2))]
                                         [0]])
            
            # updates orientation of IMU
            euler += epsilon * delta_t_gyro * gryo_vector + (1 - epsilon) * accel_rot_vector
            
            # ~~~~~~~~~~~~~~~~~~~~~~~~ CALCULATE IMU ACCELERATION ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

            # IMU positive y-axis points downward
            g = np.array([[0], [9.8], [0]])

            # rotation matrices
            R_x = np.array([[1,                    0,                   0],
                            [0,  np.cos(gyro_data.x), np.sin(gyro_data.x)],
                            [0, -np.sin(gyro_data.x), np.cos(gyro_data.x)]])
            R_y = np.array([[ np.cos(gyro_data.y), 0, np.sin(gyro_data.y)],
                            [                   0, 1,                   0],
                            [-np.sin(gyro_data.y), 0, np.cos(gyro_data.y)]])
            R_z = np.array([[ np.cos(gyro_data.z), np.sin(gyro_data.z), 0],
                            [-np.sin(gyro_data.z), np.cos(gyro_data.z), 0],
                            [                   0,                   0, 1]])
            
            # subtract gravity in IMU-frame from accelerometer data to get acceleration in navigation-frame
            acceleration = accel_vector - R_x @ R_y @ R_z @ g

            # ~~~~~~~~~~~~~~~~~~~~~~~~~~ CALCULATE IMU VELOCITY ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

            # time is also measured in in milliseconds
            ts_accel = accel_frame.get_timestamp() / 1000
            delta_t_accel = ts_accel - last_ts_accel
            last_ts_accel = ts_accel

            # velocity is the integral of acceleration, this is the best we can do lmao
            velocity += delta_t_accel * acceleration

    finally:
        pipeline.stop()

    return 0
