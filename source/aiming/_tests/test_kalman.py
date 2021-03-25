import time
import pyrealsense2 as rs
import numpy as np
import sys
import cv2

# relative imports
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print

npyFramesLocation = PATHS['npy_frames']
streamWidth = PARAMETERS['aiming']['stream_width']
streamHeight = PARAMETERS['aiming']['stream_height']

counter = 0
colors = []
depths = []
bboxs = []

try:
    while True: # THIS WILL KEEP GETTING THE NEXT FRAME UNTIL IT RUNS OUT
        counter+=1
        print("PROCESSING FRAME:",counter)
        colorFrame = np.load(npyFramesLocation+"/"+str(counter)+"color.nosync.npy").reshape(streamHeight,streamWidth,3)
        depthFrame = np.load(npyFramesLocation+"/"+str(counter)+"depth.nosync.npy").reshape(streamHeight,streamWidth)/1000
        bbox = np.load(npyFramesLocation+"/"+str(counter)+"bbox.nosync.npy").flatten()

        colors.append(colorFrame)
        depths.append(depthFrame)
        bboxs.append(bbox)
        
except Exception as e: # THIS WILL ALWAYS RUN SINCE WE RUN OUT OF FRAMES AND ARE READING FROM FILES
    print("FINISHED LOADING IMAGES")
    print("YOU CAN IGNORE THIS EXCEPTION IF YOUR DATA LOOKS GOOD (KEPT FOR DEBUGGING PURPOSES):",e)
finally:
    # DO WHATEVER YOU WANT WITH THE FRAMES
    print(depths[1])