import time
import pyrealsense2 as rs
import numpy as np
import sys
import cv2

# relative imports
from toolbox.globals import MACHINE, PATHS, PARAMETERS, print

npy_frames_location = PATHS['npy_frames']
stream_width = PARAMETERS['aiming']['stream_width']
stream_height = PARAMETERS['aiming']['stream_height']
kalman_video_path = PATHS['kalman_video']
framerate = PARAMETERS['aiming']['stream_framerate']

counter = 0
colors = []
depths = []
bboxs = []

try:
    while True: # keep getting frames until we run out
        counter+=1
        print("PROCESSING FRAME:",counter)
        color_frame = np.load(npy_frames_location+"/"+str(counter)+"color.do_not_sync.npy").reshape(stream_height,stream_width,3)
        depth_frame = np.load(npy_frames_location+"/"+str(counter)+"depth.do_not_sync.npy").reshape(stream_height,stream_width)/1000
        bbox = np.load(npy_frames_location+"/"+str(counter)+"bbox.do_not_sync.npy").flatten()

        colors.append(color_frame)
        depths.append(depth_frame)
        bboxs.append(bbox)
        
except Exception as e: # this will always run since we run out of frames
    print("FINISHED LOADING IMAGES")
    print("YOU CAN IGNORE THIS EXCEPTION IF YOUR DATA LOOKS GOOD (KEPT FOR DEBUGGING PURPOSES):",e)
finally:
    
    # debug and video, the current video will be outputted named kalman video so you can see
    frame_dimensions = (stream_width, stream_height)
    colorwriter = cv2.VideoWriter(kalman_video_path, cv2.VideoWriter_fourcc(*'mp4v'), framerate, frame_dimensions)

    for loc in range(len(colors)):
        frame = colors[loc]
        x, y, w, h = bboxs[loc].astype(int)
        # draw a bounding box rectangle and label on the frame
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0,255,0), 2)
        colorwriter.write(frame)

    colorwriter.release()