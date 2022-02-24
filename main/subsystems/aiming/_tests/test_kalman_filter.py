import numpy as np
import cv2 as cv
ix, iy = -1, -1
draw = True

bbox_width, bbox_height = 240, 120

# mouse callback function
def draw_line(event, x, y, flags, param):
    global ix, iy
    if event == cv.EVENT_MOUSEMOVE:
        if (ix < 1 or iy < 0):
            ix = x
            iy = y
        else:
            if draw:
                cv.line(img, (ix, iy), (x, y), (0, 255, 0), 1)
            ix, iy = x, y
            
img = np.zeros((720, 1280, 3), np.uint8)
cv.namedWindow('image')
cv.setMouseCallback('image', draw_line)
while(1):
    rect_img = img.copy()
    start_point = (ix - bbox_width//2, iy - bbox_height//2)
    end_point = (ix + bbox_width//2, iy + bbox_height//2)
    cv.rectangle(rect_img, start_point, end_point, (0, 255, 0), 3)
    cv.imshow('image', rect_img)
    k = cv.waitKey(1) & 0xFF
    if k == ord('c'):
        img = np.zeros((720, 1280, 3), np.uint8)
    elif k == ord('m'):
        draw = not draw
    elif k == 27:
        break
cv.destroyAllWindows()
