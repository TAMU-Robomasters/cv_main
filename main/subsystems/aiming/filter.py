import numpy as np
import filterpy
from statistics import stdev
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise
import subsystems.aiming.aiming_methods as dc

class Filter():
    def __init__(self, FPS):  # t = time interval
        t = 1/FPS
        self.f = KalmanFilter(dim_x=6, dim_z=3)
  
        self.f.x = np.array([0., 0., 0., 0., 0., 0.])    # x_pos, x_vel, y_pos, y_vel, z_pos, z_vel
        self.f.F = np.array([[1, t, 0, 0, 0, 0],
                             [0, 1, 0, 0, 0, 0],
                             [0, 0, 1, t, 0, 0],
                             [0, 0, 0, 1, 0, 0],
                             [0, 0, 0, 0, 1, t],
                             [0, 0, 0, 0, 0, 1]])     # prediction matrix
        self.f.H = np.array([[1, 0, 0, 0, 0, 0],
                             [0, 0, 1, 0, 0, 0],
                             [0, 0, 0, 0, 1, 0]])     # models to sensor data

        
        self.f.u = np.array([0., 0., 0.])             # x_acc, y_acc, z_acc
        self.f.B = np.array([[0.5 * t**2, 0, 0],
                             [t, 0, 0],
                             [0, 0.5 * t**2, 0],
                             [0, t, 0],
                             [0, 0, 0.5 * t**2],
                             [0, 0, t]])

        self.f.P *= 0.5                         # covariance matrix
        self.f.R = np.full((3, 3), 0.125)       # sensor noise
        # self.f.Q = Q_discrete_white_noise(dim=2, dt=t, var=2, block_size=3, order_by_dim = True) + 1   # uncertainty 
        # The error should be small compared to the actual value. How do we accomodate for that?    -- Carson

        # TODO: -- Carson
        #   Does this work???
        #   Testing, making this more accurate
        #   Integrate acceleration

        # "global variables"
        self.last_ts_accel = None
        self.last_ts_gyro = None
        self.euler = np.array([[0], [0], [0]])    # subject to change -- what is the initial roll/pitch/yaw of the turret?
        self.velocity = np.array([[0], [0], [0]])

        self.f.predict()

    def time_predict(self, depth):
        return depth/26

    def process_imu(self, data, frame):
        import pyrealsense2.pyrealsense2 as rs
        gyro_frame = frame.first_or_default(rs.stream.gyro)
        accel_frame = frame.first_or_default(rs.stream.accel)

        if accel_frame is not None or gyro_frame is not None:
            if accel_frame is not None:
                accel_data = accel_frame.as_motion_frame().get_motion_data() 
            if gyro_frame is not None:
                gyro_data = gyro_frame.as_motion_frame().get_motion_data()
        else:
            return None
            
        if self.last_ts_accel is None or self.last_ts_gyro is None:
            if self.last_ts_accel is None:
                self.last_ts_accel = accel_frame.get_timestamp() / 1000
            if self.last_ts_gyro is None:
                self.last_ts_gyro = gyro_frame.get_timestamp() / 1000
            return None

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
        delta_t_gyro = ts_gyro - self.last_ts_gyro
        self.last_ts_gyro = ts_gyro

        # rotation measured from accelerometers
        accel_rot_vector = np.array([[np.arctan2(accel_data.y, accel_data.x)],
                                        [np.arctan2(accel_data.z, np.sqrt((accel_data.x)**2 + (accel_data.y)**2))]
                                        [0]])
        
        # updates orientation of IMU
        self.euler += epsilon * delta_t_gyro * self.gryo_vector + (1 - epsilon) * accel_rot_vector
        
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
        delta_t_accel = ts_accel - self.last_ts_accel
        self.last_ts_accel = ts_accel

        # velocity is the integral of acceleration, this is the best we can do lmao
        self.velocity += delta_t_accel * acceleration

        # cross product of gryo data and xyz(radius) data
        data = np.array(data)
        gyro_data = np.array(gyro_data)
        gyro_vel = np.cross(gyro_data, data)

        return [gyro_vel[0], gyro_vel[1], gyro_vel[2], self.velocity[0], self.velocity[1], self.velocity[2]]

    def predict(self, data, frame):
        # center of bounding box given by (x, y, z) (x,y) in pixels z in meters
        pos_x = int(data[0])
        pos_y = int(data[1])
        pos_z = data[2]
        
        vel_data = self.process_imu(data, frame)
        if vel_data is None:
            vel_data = [0, 0, 0, 0, 0, 0]
        
        # convert to v from w (v = r*w)
        self.f.update(np.array([[pos_x], 
                                [pos_y],
                                [pos_z]]))
        self.f.predict()
        
        X = self.f.x
        U = self.f.u
    
        time = self.time_predict(pos_z)
        depth_frame = frame.getDepthFrame()
        x_in_meters = dc.world_coordinate(depth_frame,[X[0], X[2]])

        X = [x_in_meters[0] + time * (x_in_meters[1] + vel_data[0] + vel_data[3]), x_in_meters[2] + time * (x_in_meters[3] + vel_data[1] + vel_data[4]), x_in_meters[4] + time * (x_in_meters[5] + vel_data[2] + vel_data[5])]
        # X = [X[0] + time * X[1] + 0.5 * U[0] * time**2, X[2] + time * X[3] + 0.5 * U[1] * time**2, X[4] + time * X[5] + 0.5 * U[2] * time**2]
        X = dc.pixel_coordinate(X)
        location = [X[0], X[1]]
        return location

    
