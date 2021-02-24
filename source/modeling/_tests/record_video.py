import time
import pyrealsense2 as rs
import numpy as np
import sys
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

pipeline = rs.pipeline()                                            
config = rs.config()                                                
config.enable_stream(rs.stream.depth, streamWidth, streamHeight, rs.format.z16, framerate)  
config.enable_stream(rs.stream.color, streamWidth, streamHeight, rs.format.bgr8, framerate) 
pipeline.start(config)

t0 = time.time()
framesList = []
status = True

while (time.time()-t0) <timeRecord:
    frames = pipeline.wait_for_frames()     
    color_frame = frames.get_color_frame()  

    if not color_frame:
        print("INVALID FRAME, SKIPPING")
        continue

    color_image = np.asanyarray(color_frame.get_data())
    image = Image(color_image) 
    framesList.append(image.img)

if status:
    Video.create_from_frames(framesList, save_to=PATHS["record_video_output"],fps=framerate)
