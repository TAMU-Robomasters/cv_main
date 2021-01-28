import numpy as np
import matplotlib.pyplot as plt
import filterpy
from statistics import stdev
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise

class Filter():
    def __init__(self, t):  # t = time interval
        self.f = KalmanFilter(dim_x=4, dim_z=2)
  
        self.f.x = np.array([0., 0., 0., 0.])    # x_pos, x_vel, y_pos, y_vel
        self.f.F = np.array([[1, t, 0, 0],
                             [0, 1, 0, 0],
                             [0, 0, 1, t],
                             [0, 0, 0, 1]])     # prediction matrix
        self.f.H = np.array([[1, 0, 0, 0],
                             [0, 0, 1, 0]])     # models to sensor data
        self.f.P *= 0.5                         # covariance matrix
        self.f.R = np.full((2, 2), 0.125)      # sensor noise
        self.f.Q = Q_discrete_white_noise(dim=4, dt=t, var=2) + 1   # uncertainty

        self.f.predict()

    def predict(self, bbox):
        # center of bounding box given by (x, y, w, h)
        pos_x = int(bbox[0] + bbox[2]/2)
        pos_y = int(bbox[1] + bbox[3]/2)

        self.f.update(np.array([[pos_x], 
                                [pos_y]]))
        self.f.predict()

        return self.f.x
        