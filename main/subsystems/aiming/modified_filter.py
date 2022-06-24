"""
    File name         : KalmanFilter.py
    Description       : KalmanFilter class used for object tracking
    Author            : Rahmad Sadli
    Date created      : 20/02/2020
    Python Version    : 3.7
"""

import numpy as np
import matplotlib.pyplot as plt


class KalmanFilter(object):
    def __init__(self, FPS):
        """
        :param dt: sampling time (time for 1 cycle)
        :param u_x: acceleration in x-direction
        :param u_y: acceleration in y-direction
        :param std_acc: process noise magnitude
        :param horizonal_stdev_meas: standard deviation of the measurement in x-direction
        :param vertical_stdev_meas: standard deviation of the measurement in y-direction
        """
        self.std_acc = 1
        self.horizonal_stdev_meas = 1
        self.vertical_stdev_meas = 1
        self.z_std_meas = 1

        # Define sampling time
        self.dt = 1 / FPS

        # Define the  control input variables
        self.u = np.matrix([[1], [1], [1]])

        # Intial State
        self.x = np.matrix(
            [[0.0], [0.0], [0.0], [0.0], [0.0], [0.0]]
        )  # x_pos, y_pos, z_pos, x_vel, y_vel, z_vel

        # Define the State Transition Matrix A
        self.A = np.matrix(
            [
                [1, 0, 0, self.dt, 0, 0],
                [0, 1, 0, 0, self.dt, 0],
                [0, 0, 1, 0, 0, self.dt],
                [0, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 1],
            ]
        )

        # Define the Control Input Matrix B
        self.B = np.matrix(
            [
                [(self.dt**2) / 2, 0, 0],
                [0, (self.dt**2) / 2, 0],
                [0, 0, (self.dt**2) / 2],
                [self.dt, 0, 0],
                [0, self.dt, 0],
                [0, 0, self.dt],
            ]
        )

        # Define Measurement Mapping Matrix
        self.H = np.matrix([[1, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0]])

        # Initial Process Noise Covariance
        self.Q = (
            np.matrix(
                [
                    [(self.dt**4) / 4, 0, 0, (self.dt**3) / 2, 0, 0],
                    [0, (self.dt**4) / 4, 0, 0, (self.dt**3) / 2, 0],
                    [0, 0, (self.dt**4) / 4, 0, 0, (self.dt**3) / 2],
                    [(self.dt**3) / 2, 0, 0, self.dt**2, 0, 0],
                    [0, (self.dt**3) / 2, 0, 0, self.dt**2, 0],
                    [0, 0, (self.dt**3) / 2, 0, 0, self.dt**2],
                ]
            )
            * self.std_acc**2
        )

        # Initial Measurement Noise Covariance
        self.R = np.matrix(
            [
                [self.horizonal_stdev_meas**2, 0, 0],
                [0, self.vertical_stdev_meas**2, 0],
                [0, 0, self.z_std_meas**2],
            ]
        )

        # Initial Covariance Matrix
        self.P = np.eye(self.A.shape[1])

    def predict(self):
        # Refer to :Eq.(9) and Eq.(10)  in https://machinelearningspace.com/object-tracking-simple-implementation-of-kalman-filter-in-python/?preview_id=1364&preview_nonce=52f6f1262e&preview=true&_thumbnail_id=1795

        # Update time state
        # x_k =Ax_(k-1) + Bu_(k-1)     Eq.(9)
        self.x = np.dot(self.A, self.x) + np.dot(self.B, self.u)

        # Calculate error covariance
        # P= A*P*A' + Q               Eq.(10)
        self.P = np.dot(np.dot(self.A, self.P), self.A.T) + self.Q
        return self.x[0:3]

    def update(self, z):

        # Refer to :Eq.(11), Eq.(12) and Eq.(13)  in https://machinelearningspace.com/object-tracking-simple-implementation-of-kalman-filter-in-python/?preview_id=1364&preview_nonce=52f6f1262e&preview=true&_thumbnail_id=1795
        # S = H*P*H'+R
        S = np.dot(self.H, np.dot(self.P, self.H.T)) + self.R

        # Calculate the Kalman Gain
        # K = P * H'* inv(H*P*H'+R)
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(S))  # Eq.(11)

        self.x = np.round(self.x + np.dot(K, (z - np.dot(self.H, self.x))))  # Eq.(12)

        I = np.eye(self.H.shape[1])

        # Update error covariance matrix
        self.P = (I - (K * self.H)) * self.P  # Eq.(13)
        return self.x[0:3]
