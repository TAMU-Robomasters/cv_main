from toolbox.globals import MACHINE, PATHS, PARAMETERS, print
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
    """
    @bounding_boxes - this is a list of boxes
                      each box (should) corrispond to an armor-plate on an enemy vehicle
                      the box itself is a list containing 4 things (in this order)
                      - integer: the x-coordinate of the top left corner of the box (measured in pixels)
                      - integer: the y-coordinate of the top left corner of the box (measured in pixels)
                      - integer: the width of the box (measured in pixels)
                      - integer: the height of the box (measured in pixels)
    @@returns:
        a list (or tuple) with two elements
        - the x-coordinate of where to aim the barrel
        - the y-coordinate of where to aim the barrel
        
        note: in the future this function might return more data, like the depth/distance to the target
    """
    
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
