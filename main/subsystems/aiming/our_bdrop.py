#
# TAMU Robomaster
# Root(time) finder
# Written by Albert M
#

import numpy as np
import time

# xR = float(input("X robot: "))
# yR = int(input("Y robot: "))
# zR = int(input("Z robot: "))

# v_x = float(input("Velocity x component: "))
# v_y = int(input("Velocity y component: "))
# v_z = int(input("Velocity z component: "))

# a_x = float(input("Acceleration x component: "))
# a_y = int(input("Acceleration y component: "))
# a_z = int(input("Acceleration z component: "))

# xR = 5
# yR = 3
# zR = 2

# v_x = 1
# v_y = 1
# v_z = 1

# a_x = 0.25
# a_y = 0.25
# a_z = 0.25

# L = 0.5

# v0 = 28.0
# g = 4.9

def find_root(x, y, z, vx, vy, vz, ax, ay, az, l, v0):
    c4 = 0.25*ax**2 + (0.5*ay - g)**2 + 0.25*az**2   # For for coefficient of t^4
    c3 = vx*ax + 2*vy*(0.5*ay - g) + vz*az   # For coefficient of t^3 
    c2 = (vx**2 +ax*x) + 2*y*(0.5*ay - g) + (vz**2 +az*z) - v0**2    # For coefficient of t^2
    c1 = 2*x*vx + 2*y*vy + 2*z*vz - 2*v0*l   # For coefficient of t
    c0 = x**2 + y**2 + z**2 - l**2   # Just Standalone numbers
    equation_coef = [c4, c3, c2, c1, c0] # listing all coefficients
    root = np.roots(equation_coef)

    return root

def find_phee(y, vy, ay, l, t, v0):
    return np.arcsin((y + vy*t + 0.5*ay*(t**2) - g*(t**2))/(l + v0*t))

def find_theta(x, vx, ax, l, t, p):
    return np.arcsin((x + vx*t + 0.5*ax*(t**2))/(l + v0*t))/np.cos(p)





def angle_getter(xR, yR, zR, v_x, v_y, v_z, a_x, a_y, a_z, l, v0):

    time_ans = find_root(xR, yR, zR, v_x, v_y, v_z, a_x, a_y, a_z, L, v0)
    # print(time_ans)

    phee = find_phee(yR, v_y, a_y, L, time_ans, v0)
    # print("phee", phee)

    theta = find_theta(xR, v_x, a_x, L, time_ans, phee, , v0)
    # print("theta", theta)

    return (theta, phee)