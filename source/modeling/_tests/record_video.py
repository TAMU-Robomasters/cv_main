import time
import pyrealsense2 as rs
import numpy as np
import sys
import cv2
# relative imports
from toolbox.video_tools import Video
from toolbox.image_tools import Image
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print

streamWidth = PARAMETERS['aiming']['stream_width']
streamHeight = PARAMETERS['aiming']['stream_height']
framerate = PARAMETERS['aiming']['stream_framerate']
gridSize = PARAMETERS['aiming']['grid_size']
frameAmount = PARAMETERS['videostream']['testing']['camera_frames']
timeRecord = PARAMETERS['videostream']['testing']['record_time']
colorVideoLocation = PATHS['record_video_output_color']
depthVideoLocation = PATHS['record_video_output_depth']


pipeline = rs.pipeline()                                            
config = rs.config()                                                
config.enable_stream(rs.stream.depth, streamWidth, streamHeight, rs.format.z16, framerate)  
config.enable_stream(rs.stream.color, streamWidth, streamHeight, rs.format.bgr8, framerate) 
pipeline.start(config)

frame_dimensions = (streamWidth, streamHeight)
colorwriter = cv2.VideoWriter(colorVideoLocation, cv2.VideoWriter_fourcc(*'mp4v'), framerate, frame_dimensions)
depthwriter = cv2.VideoWriter(depthVideoLocation, cv2.VideoWriter_fourcc(*'mp4v'), framerate, frame_dimensions)

t0 = time.time()
try:
    while (time.time()-t0)<timeRecord:
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_color_frame()

        if not color_frame or not depth_frame:
            continue

        color_image = np.asanyarray(color_frame.get_data())
        depth_image = np.asanyarray(depth_frame.get_data())
        colorwriter.write(color_image)
        depthwriter.write(color_image)
finally:
    colorwriter.release()
    depthwriter.release()
    pipeline.stop()