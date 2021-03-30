import numpy as np
import matplotlib.pyplot as plt
import filterpy
from statistics import stdev
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise

class Filter():
    def __init__(self, t):  # t = time interval
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
        self.f.P *= 0.5                         # covariance matrix
        self.f.R = np.full((3, 3), 0.125)       # sensor noise
        # self.f.Q = Q_discrete_white_noise(dim=2, dt=t, var=2, block_size=3, order_by_dim = True) + 1   # uncertainty 
        # The error should be small compared to the actual value. How do we accomodate for that?    -- Carson

        # TODO: -- Carson
        #   Does this work???
        #   Testing, making this more accurate
        #   Integrate acceleration

        self.f.predict()

    def predict(self, data):
        # center of bounding box given by (x, y, z)
        pos_x = int(data[0])
        pos_y = int(data[1])
        pos_z = int(data[2])

        self.f.update(np.array([[pos_x], 
                                [pos_y],
                                [pos_z]]))
        self.f.predict()

        return self.f.x
        