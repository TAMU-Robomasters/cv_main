import pyrealsense2 as rs
import numpy as np
import cv2
from toolbox.globals import PARAMETERS,print

# PASS pipeline ON FUNCTION CALL WHEN INTEGRATED WITH MAIN SINCE CAMERA FEED IS INITIALIZED IN get_live_video_frame

streamWidth = PARAMETERS['aiming']['stream_width']
streamHeight = PARAMETERS['aiming']['stream_height']
framerate = PARAMETERS['aiming']['stream_framerate']
gridSize = PARAMETERS['aiming']['grid_size']

pipeline = rs.pipeline()                                            # declares and initializes the pipeline variable
config = rs.config()                                                # declares and initializes the config variable for the pipeline
config.enable_stream(rs.stream.depth, streamWidth, streamHeight, rs.format.z16, framerate)  # this starts the depth stream and sets the size and format
config.enable_stream(rs.stream.color, streamWidth, streamHeight, rs.format.bgr8, framerate) # this starts the color stream and set the size and format
profile = pipeline.start(config)

# This creates a 9 by 9 grid of points within the given bounding box and stores each of the points distance in an array
def getDistFromArray(depth_frame_array, bbox):
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
    
    distances = np.sort(distances)          # sorts the distances from least to greatest
    distances = distances[distances!=0.0]   # removes all occurances of 0.0 (areas where there is not enough data return 0.0 as depth)
    median = np.median(distances)           # gets the median from the array
    std = np.std(distances)                 # gets the standard deviation from th array
    modifiedDistances = []                  # initializes a new array for removing outlier numbers
    # goes through distances array and adds any values that are less than X*standard deviations and ignores the rest
    for i in range(np.size(distances)):
        if abs(distances[i] - median) < 1.5 * std: # tune the standard deviation range for better results
            modifiedDistances = np.append(modifiedDistances,distances[i])

    modifiedDistances = np.sort(modifiedDistances)
    distance = (np.mean(modifiedDistances)+np.median(modifiedDistances))/2
    return distance

# bbox[x coordinate of the top left of the bounding box, y coordinate of the top left of the bounding box, width of box, height of box]
def DistanceInBox(bbox):
    try:
        frames = pipeline.wait_for_frames()     # gets all frames
        depth_frame = frames.get_depth_frame()  # gets the depth frame
        color_frame = frames.get_color_frame()  # gets the color frame 
        if not depth_frame or not color_frame:  # if there is no aligned_depth_frame or color_frame then leave the loop
            return None
        # we turn the depth and color frames into numpy arrays because we need to draw a rectangle and stack the two arrays
        depth_image = np.asanyarray(depth_frame.get_data()) 
        # causes 1FPS Drop
        return getDistFromArray(depth_image, bbox)     # gets the distance for the normal depth image
    finally:
        pipeline.stop()
    return None


#bbox = [410,140,65,120]

#while True:
#	print(DistanceInBox(bbox))
