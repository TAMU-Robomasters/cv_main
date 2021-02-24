from math import *
import numpy as np
import cv2 as cv
import time
bboxes = []

w = 50
h = 0.5 * w

# starts in the top left constant motion southeast, no change in depth
for t in range(100):
    x = 2 * t + 100
    y = t + 100
    w = 50
    h = 0.5 * w
    bboxes.append([x, y, w, h])

# constant acceleration north east getting farther away
x0, y0, w0, h0 = x, y, w, h
for t in range(30):
    x = t**1.5 + x0
    y = -t**1.2 + y0
    w = w0 - t*2
    h = w * 0.5
    bboxes.append([x, y, w, h])

# exponential increase towards southwest getting closer
x0, y0, w0, h0 = x, y, w, h
for t in range(10):
    x = x0 - t * 20
    y = t**2 + y0
    w = w0 + t*2
    h = w * 0.5
    bboxes.append([x, y, w, h])


# graph of sin moving closer and farther towards east
x0, y0, w0, h0 = x, y, w, h
for t in range(10):
    x = sin(t) + x0
    y = sin(t) + y0
    w = w0 + sin(t)
    h = w * 0.5
    bboxes.append([x, y, w, h])





# print(bboxes)
for t in bboxes:
    startpoint = (int(t[0]),int(t[1]))
    endpoint = (int(t[0]+t[2]),int(t[1]+t[3]))
    color = (0,255,0)
    thickness = 3
    # print(startpoint)
    # print(endpoint)
    img = np.zeros((408,848,3), np.uint8)
    cv.rectangle(img, startpoint, endpoint, color, thickness)
    # cv.rectangle(img, startpoint, endpoint, color, thickness)
    time.sleep(0.05)
    cv.imshow("hello",img)
    k = cv.waitKey(1)
    if k == 27 & 0xFF:
            break
