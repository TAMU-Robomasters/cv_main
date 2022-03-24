from math import dist
import numpy as np
import cv2 as cv
from subsystems.aiming.ModifiedKalmanFilter import KalmanFilter
bx, by = -1, -1     # bounding box x and y
kx, ky = -1, -1     # kalman filter x and y
draw = False

armor_plate_width, armor_plate_height = 0.235, 0.127
res_width, res_height = 1280, 720
fov_width, fov_height = np.radians(58), np.radians(87)
depth = 2

# mouse callback function
def draw_line(event, x, y, flags, param):
    global bx, by
    if event == cv.EVENT_MOUSEMOVE:
        if (bx >= 0 and by >= 0) and draw:
            cv.line(img, (bx, by), (x, y), (0, 255, 0), 1)
        bx, by = x, y
            
img = np.zeros((res_height, res_width, 3), np.uint8)
cv.namedWindow('image')
cv.setMouseCallback('image', draw_line)

kf = KalmanFilter(30)

while(1):
    rect_img = img.copy()
    
    # draw bounding box
    bbox_width = int(armor_plate_width * 1000)
    bbox_height = int(armor_plate_height * 1000)
    start_point = (bx - bbox_width//2, by - bbox_height//2)
    end_point = (bx + bbox_width//2, by + bbox_height//2)
    cv.rectangle(rect_img, start_point, end_point, (0, 255, 0), 3)
    
    # make kalman prediction
    kf.update(np.array([[bx], [by], [depth]]))
    kf.predict()
    x, y = tuple(kf.x.getA().flatten().astype(int)[:2].tolist())
    if (kx >= 0 and ky >= 0) and draw:
        cv.line(img, (kx, ky), (x, y), (255, 0, 0), 1)
        cv.circle(rect_img, (kx, ky), 5, (0, 0, 255), -1)
    kx, ky = x, y
    
    cv.imshow('image', rect_img)
    k = cv.waitKey(1) & 0xFF
    if k == ord('c'):
        img = np.zeros((res_height, res_width, 3), np.uint8)
    elif k == ord('m'):
        draw = not draw
    elif k == 27:
        break
cv.destroyAllWindows()
