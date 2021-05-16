import numpy as np
import filterpy
from statistics import stdev
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise
import source.aiming.depth_camera as dc


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

        self.f.predict()

    def timePredict(self, time):
        return X

    def predict(self, data):
        # center of bounding box given by (x, y, z)
        pos_x = int(data[0])
        pos_y = int(data[1])
        pos_z = int(data[2])

        self.f.update(np.array([[pos_x], 
                                [pos_y],
                                [pos_z]]))
        self.f.predict()
        
        X = self.f.x
        U = self.f.u
        # print("pos_z:", pos_z)
        # time = dc.travelTime(pos_z)
        time = 1
        # print("time: ", time)
        print(U)
        X = [X[0] + time * X[1], X[2] + time * X[3], X[4] + time * X[5]]
        # X = [X[0] + time * X[1] + 0.5 * U[0] * time**2, X[2] + time * X[3] + 0.5 * U[1] * time**2, X[4] + time * X[5] + 0.5 * U[2] * time**2]
        location = [X[0], X[1]]
        return location

    
