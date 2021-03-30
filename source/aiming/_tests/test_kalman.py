import time
import numpy as np
import sys
import cv2
import source.aiming.filter as f
import source.aiming.depth_camera as dc

# relative imports
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print

npyFramesLocation = PATHS['npy_frames']
streamWidth = PARAMETERS['aiming']['stream_width']
streamHeight = PARAMETERS['aiming']['stream_height']
kalmanVideoPath = PATHS['kalman_video']
framerate = PARAMETERS['aiming']['stream_framerate']
gridSize = PARAMETERS['aiming']['grid_size']

counter = 0
colors = []
depths = []
bboxs = []
preds = []
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
    # DO WHATEVER YOU WANT WITH THE FRAMES HERE


    # filter = f.Filter(5)

    filter = f.Filter(2)
    for i in range(len(depths)):
        bbox = bboxs[i]
        depth = depths[i]
        if ((bbox == [-1, -1, -1, -1]).all()):
            preds.append(np.array([-1, -1, -1, -1]))
            # filter = f.Filter(1000)
            continue
    
        depth_value = dc.getDistFromArray(depth, bbox, gridSize)
        X = filter.predict([bbox[0]+bbox[2]/2, bbox[1]+bbox[3]/2, depth_value])
        preds.append(np.array([X[0]-bbox[2]/2, X[2]-bbox[3]/2, bbox[2], bbox[3]]))
        pred = preds[i]
        print(bbox[0], "", pred)

        
    




    # debug and video, the current video will be outputted named kalman video so you can see
    frame_dimensions = (streamWidth, streamHeight)
    colorwriter = cv2.VideoWriter(kalmanVideoPath, cv2.VideoWriter_fourcc(*'mp4v'), framerate, frame_dimensions)

    for loc in range(len(colors)):
        frame = colors[loc]
        bbox = preds[loc]
        x, y, w, h = bboxs[loc].astype(int)
        if ((bbox == [-1, -1, -1, -1]).all() == False):
            x1, y1, w1, h1 = bbox.astype(int)
            cv2.rectangle(frame, (x1, y1), (x1 + w1, y1 + h1), (255,0,0), 2)

        
        # draw a bounding box rectangle and label on the frame
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0,255,0), 2)
        colorwriter.write(frame)

    colorwriter.release()