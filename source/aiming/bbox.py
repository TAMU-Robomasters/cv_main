from math import *

bboxes = []

w = 50
h = 0.5 * w

# constant motion northeast, no change in depth
for t in range(10):
    x = t + 3
    y = 2 * t
    w = 50
    h = 0.5 * w
    bboxes.append([x, y, w, h])

# constant acceleration
x0, y0, w0, h0 = x, y, w, h
for t in range(10):
    x = -t**2 + x0