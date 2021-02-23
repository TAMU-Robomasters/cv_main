import numpy as np
import cv2
from toolbox.globals import PARAMETERS,print


def getDistFromArray(depth_frame_array, bbox,gridSize):
    xTopLeft = bbox[0] 
    yTopLeft = bbox[1]
    width = bbox[2]
    height = bbox[3]
    # this is used to add to the currentX and currentY so that we can get the different points in the 9x9 grid
    x_interval = width/gridSize
    y_interval = height/gridSize
    # stores the x and y of the last point in the grid we got the distance from
    currX = 0
    currY = 0
    distances = np.array([])
    # double for loop to go through 2D array of 9x9 grid
    for i in range(gridSize):
        currX += x_interval # add the interval you calculated to traverse through the 9x9 grid
        for j in range(gridSize):
            currY += y_interval # add the interval you calculated to traverse through the 9x9 grid
            # gets the distance of the point from the depth frame on the grid and appends to the array
            distances = np.append(distances, depth_frame_array[int(yTopLeft+currY)][int(xTopLeft+currX)]/1000)
        currY = 0
    
    distances = distances[distances!=0.0]   # removes all occurances of 0.0 (areas where there is not enough data return 0.0 as depth)
    median = np.median(distances)           # gets the median from the array
    std = np.std(distances)                 # gets the standard deviation from th array
    modifiedDistances = []                  # initializes a new array for removing outlier numbers
    # goes through distances array and adds any values that are less than X*standard deviations and ignores the rest
    for i in range(np.size(distances)):
        if abs(distances[i] - median) < 1.5 * std: # tune the standard deviation range for better results
            modifiedDistances = np.append(modifiedDistances,distances[i])

    distance = (np.mean(modifiedDistances)+np.median(modifiedDistances))/2
    return distance