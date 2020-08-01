from filterpy.common import kinematic_kf
from filterpy.kalman import ExtendedKalmanFilter
import time
import numpy as np
import filterpy as fp
from filterpy.kalman import IMMEstimator

np.set_printoptions(suppress=True)
order = 1
kf1 = kinematic_kf(dim=2, order=order)
kf2 = ExtendedKalmanFilter(4, 2)
kf2.Q *= 0  # no prediction error in second filter
filters = [kf1, kf2]
mu = [0.5, 0.5]  # filter probability
trans = np.array([[0.97, 0.03], [0.03, 0.97]])
imm = IMMEstimator(filters, mu, trans)


def aim(bounding_boxes):
    # TODO: Needs testing
    # TODO: Finalize on input contract
    if len(bounding_boxes) == 0:
        return imm.x_prior[0], imm.x_prior[2]  # return last result
    if isinstance(bounding_boxes[0], list):
        bbox = bounding_boxes[0]
    else:
        bbox = bounding_boxes  # x,y,w,h

    x = bbox[0]
    y = bbox[1]

    z = np.array([[x], [y]])
    imm.update(z)
    imm.predict()

    new_vals = imm.x.T[0]
    if order == 1:
        xp = int(new_vals[0])
        yp = int(new_vals[2])
    elif order == 2:
        xp = int(new_vals[0])
        yp = int(new_vals[3])

    return xp, yp
