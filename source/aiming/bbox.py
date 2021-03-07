from math import *
import numpy as np
import cv2 as cv
import time
from filter import Filter


bboxes = []

# x = 0
# y = 300
w = 100
h = 0.5 * w

# #constant acceleration north east getting farther away
# for t in range():
#     x += t**1.1
#     y += -t**1.1
#     w = w
#     h = w * 0.5
#     bboxes.append([x, y, w, h])

# starts in the top left constant motion southeast, no change in depth
for t in range(100):
    x = 2 * t + 100
    y = t + 100
    w = 100
    h = 0.5 * w
    bboxes.append([x, y, w, h])

# constant motion north east, getting farther away
x0, y0, w0, h0 = x, y, w, h
for t in range(100):
    x = 2 * t + x0
    y = -t + y0
    w = w0 - 1/3*t
    h = 0.5 * w
    bboxes.append([x, y, w, h])

# no motion, getting closer
x0, y0, w0, h0 = x, y, w, h
for t in range(100):
    x = x0
    y = y0
    w = w0 + 1/2*t
    h = 0.5 * w
    bboxes.append([x, y, w, h])

# move just westward
x0, y0, w0, h0 = x, y, w, h
for t in range(100):
    x = x0 - t
    y = y0
    w = w0
    h = 0.5 * w
    bboxes.append([x, y, w, h])

# #constant acceleration north east getting farther away
# x0, y0, w0, h0 = x, y, w, h
# for t in range(30):
#     x = t**1.5 + x0
#     y = -t**1.2 + y0
#     w = w0 - t*2
#     h = w * 0.5
#     bboxes.append([x, y, w, h])

# exponential increase towards southwest getting closer
# x0, y0, w0, h0 = x, y, w, h
# for t in range(10):
#     x = x0 - t * 20
#     y = t**2 + y0
#     w = w0 + t*2
#     h = w * 0.5
#     bboxes.append([x, y, w, h])


# graph of sin moving closer and farther towards east
# x0, y0, w0, h0 = x, y, w, h
# for t in range(10):
#     x = sin(t) + x0
#     y = sin(t) + y0
#     w = w0 + sin(t)
#     h = w * 0.5
#     bboxes.append([x, y, w, h])








# filter = Filter(0.1)
# print(filter.f.P)

# for i in range(100):
#     filter.predict([-0.4, 0.2, 50])
#     print(filter.f.x)


# for t in bboxes:
#     x = int(t[0] + t[2]/2)
#     y = int(t[1] + t[3]/2)
#     z = 100/(int(t[2]))
#     filter.predict([x,y,z])
#     print(filter.f.x)

# draw the motion
filter = Filter(0.1)
for t in bboxes:
    # draw the bounding box
    startpoint = (int(t[0]),int(t[1]))
    endpoint = (int(t[0]+t[2]),int(t[1]+t[3]))
    color = (0,255,0)
    thickness = 3
    img = np.zeros((408,848,3), np.uint8)
    cv.rectangle(img, startpoint, endpoint, color, thickness)

    # draws the prediction
    x = int(t[0] + t[2]/2)
    y = int(t[1] + t[3]/2)
    z = 100/(int(t[2]))
    filter.predict([x,y,z])
    data = filter.f.x
    # abs(int(data[4])*10)
    cv.circle(img, (int(data[0]), int(data[2])), 3, color, 1)
    # cv.rectangle(img, startpoint, endpoint, color, thickness)
    time.sleep(0.05)
    cv.imshow("hello",img)
    k = cv.waitKey(1)
    if k == 27 & 0xFF:
            break