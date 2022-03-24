import cv2
import numpy as np
from math import sqrt,degrees,acos,asin
from toolbox.globals import path_to, config, print

cap = cv2.VideoCapture(path_to.rune_test_video)
small_image = cv2.imread(path_to.R_test_image) # THE SMALL IMAGE WE USE WILL BE BASED ON THE QUALITY OF OUR CAMERA DUE TO TEMPLATE MATCHING
blue_light_bound = config.aiming.blue_light
blue_dark_bound = config.aiming.blue_dark
area_arrow_bound = config.aiming.area_arrow_bound
center_image_offset = config.aiming.center_image_offset
min_area = config.aiming.min_area
r_timer = config.aiming.r_timer

counter = 0
mp_x, mp_y = 0,0
ax, ay = 0,0

while(True):
    ret, frame = cap.read()
    if frame is None:
        break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV) # convert from BGR to HSV
    frame = cv2.GaussianBlur(frame,(5,5),cv2.BORDER_DEFAULT)
    # cv2.rectangle(frame,(mp_x-5,mp_y-5),(mp_x+5,mp_y+5),(200,200,120),5)   # draw rectangle around matched template

    # set lower and upper bound on color to only get blue and find the contours
    blue_light = np.array(blue_light_bound) 
    blue_dark = np.array(blue_dark_bound) 
    mask = cv2.inRange(hsv, blue_light, blue_dark)
    contours,_ = cv2.findContours(mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE)
    bounding_boxes = []

    # go through every small filtered contour and if it is within a certain size, set its x and y value to respective arrays for arrows 
    arrx = []
    arry = []
    for contour in contours:        
        area = cv2.contourArea(contour)
        if area > area_arrow_bound[0] and area < area_arrow_bound[1]:
            x,y,w,h = cv2.boundingRect(contour)
            ax,ay = x+w/2,y+h/2
            arrx.append(ax-mp_x)
            arry.append(ay-mp_y)


    arrx = np.array(arrx)
    arry = np.array(arry)
    medianx = np.median(arrx)
    stdx = np.std(arrx)
    mediany = np.median(arry)
    stdy = np.std(arry)

    # filter outliers for arrows and the center point by replacing the point with its respective median x and y values if more than 2 standard deviations away from the median and use median to avoid outliers
    for i in range(np.size(arrx)):
        box = [arrx[i]+mp_x,arry[i]+mp_y]
        if(abs(arrx[i] - medianx) > 2 * stdx) or (abs(arry[i] - mediany) > 2 * stdy) or (box[0]+10 >= mp_x-10 and mp_x+10 >= box[0]) and (box[1]+10 >= mp_y and mp_y+10 >= box[1]):
            arrx[i] = medianx
            arry[i] = mediany


    # draw boxes around all the remaining arrows
    # for i in range(len(arrx)):
        # print(arrx[i],arry[i])
        # cv2.rectangle(frame,(int(arrx[i])-5+mp_x,int(arry[i])-5+mp_y),(int(arrx[i])+5+mp_x,int(arry[i])+5+mp_y),(120,200,260),3)
 

    # set arrow position to the median position
    ax = np.median(arrx)+mp_x 
    ay = np.median(arry)+mp_y


    # every 30 frames get the new position of the r image
    if counter%r_timer == 0:
        result = cv2.matchTemplate(small_image, frame, cv2.TM_SQDIFF_NORMED)
        mn,mx,mn_loc, mx_loc = cv2.minMaxLoc(result)
        mp_x,mp_y = mn_loc
        mp_x+=center_image_offset
        mp_y+=center_image_offset
    counter+=1

    for contour in contours:
        area = cv2.contourArea(contour)
        
        if area> min_area: # filter contour based on minimum area
            x,y,w,h = cv2.boundingRect(contour)
            status = True

            # go through every box to make sure the current box doesn't overlap, if it does then find the one with the largest distance from the center and keep that one
            for box_index in range(len(bounding_boxes)):
                box = bounding_boxes[box_index]
                if (box[0]+box[2] >= x and x+w >= box[0]) and (box[1]+box[3] >= y and y+h >= box[1]):
                    height,width = frame.shape[:2]
                    cx_box = x+w/2
                    cy_box = y+h/2
                    cx_diff = mp_x - cx_box
                    cy_diff = mp_y - cy_box
                    dist_from_center = sqrt(cx_diff**2+cy_diff**2)
                    if dist_from_center>box[5]:
                        bounding_boxes.remove(box)
                        bounding_boxes.append([x,y,w,h,area,dist_from_center])
                    status = False
                    break
            if status:
                    height,width = frame.shape[:2]
                    cx_box = x+w/2
                    cy_box = y+h/2
                    cx_diff = mp_x - cx_box
                    cy_diff = mp_y - cy_box
                    dist_from_center = sqrt(cx_diff**2+cy_diff**2)
                    bounding_boxes.append([x,y,w,h,area,dist_from_center])

    # calculate average distance from center for the bounding boxes
    average_distance = 0
    for box in bounding_boxes:
        average_distance += box[5]
    if average_distance!=0:
        average_distance/=len(bounding_boxes)
        average_distance*=.5

    # get rid of faulty boxes by checking if their distance is below average distance times a certain bias
    boxes = []
    for box in bounding_boxes:
        if box[5]>average_distance:
            boxes.append(box)
    bounding_boxes=boxes

    # calculate the angle between every bounding box and the arrow with respect to the center using a dot b = |a||b|cos(theta) and set the bounding box to the one with the smallest angle
    best_box,angle = None,360
    arrow_to_center=np.array([ax-mp_x,ay-mp_y])
    for box in bounding_boxes:
        # cv2.line(frame, (int(box[0]+1/2*box[2]), int(box[1]+1/2*box[3])), (mp_x, mp_y), (0, 255, 0), thickness=3) # draw arrow from center of R to center of box
        box_to_center = np.array([box[0]+1/2*box[2]-mp_x,box[1]+1/2*box[3]-mp_y])
        dot_product = np.dot(arrow_to_center,box_to_center)
        mag1 = sqrt(np.sum(arrow_to_center**2))
        mag2 = sqrt(np.sum(box_to_center**2))
        angle2 =  degrees(acos(dot_product/(mag1*mag2)))

        best_box, angle = (best_box,angle) if (angle2>angle) else (box,angle2)

    if best_box:
        cv2.rectangle(frame,(best_box[0],best_box[1]),(best_box[0]+best_box[2],best_box[1]+best_box[3]),(0,255,0),5)
    
    # cv2.imshow('mask',mask) 
    cv2.imshow('frame',frame)


    if cv2.waitKey(1) & 0xFF == ord('q'):
        break