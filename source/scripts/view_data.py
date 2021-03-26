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
kalmanVideoPath = PATHS['kalman_video']
framerate = PARAMETERS['aiming']['stream_framerate']

counter = 0
colors = []
depths = []
bboxs = []

try:
    while True: # keep getting frames until we run out
        counter+=1
        print("PROCESSING FRAME:",counter)
        colorFrame = np.load(npyFramesLocation+"/"+str(counter)+"color.nosync.npy").reshape(streamHeight,streamWidth,3)
        depthFrame = np.load(npyFramesLocation+"/"+str(counter)+"depth.nosync.npy").reshape(streamHeight,streamWidth)/1000
        bbox = np.load(npyFramesLocation+"/"+str(counter)+"bbox.nosync.npy").flatten()

        colors.append(colorFrame)
        depths.append(depthFrame)
        bboxs.append(bbox)
        
except Exception as e: # this will always run since we run out of frames
    print("FINISHED LOADING IMAGES")
    print("YOU CAN IGNORE THIS EXCEPTION IF YOUR DATA LOOKS GOOD (KEPT FOR DEBUGGING PURPOSES):",e)
finally:
    
    # debug and video, the current video will be outputted named kalman video so you can see
    frame_dimensions = (streamWidth, streamHeight)
    colorwriter = cv2.VideoWriter(kalmanVideoPath, cv2.VideoWriter_fourcc(*'mp4v'), framerate, frame_dimensions)

    for loc in range(len(colors)):
        frame = colors[loc]
        x, y, w, h = bboxs[loc].astype(int)
        # draw a bounding box rectangle and label on the frame
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0,255,0), 2)
        colorwriter.write(frame)

    colorwriter.release()