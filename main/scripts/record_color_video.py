import time
import pyrealsense2.pyrealsense2 as rs
import numpy as np
import cv2

# relative imports
from toolbox.video_tools import Video
from toolbox.image_tools import Image
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print

streamWidth = PARAMETERS['aiming']['stream_width']
streamHeight = PARAMETERS['aiming']['stream_height']
framerate = PARAMETERS['aiming']['stream_framerate']
timeRecord = PARAMETERS['videostream']['testing']['record_time']
colorVideoLocation = PATHS['record_video_output_color']

pipeline = rs.pipeline()                                            
config = rs.config()                                                
config.enable_stream(rs.stream.depth, streamWidth, streamHeight, rs.format.z16, framerate)  
config.enable_stream(rs.stream.color, streamWidth, streamHeight, rs.format.bgr8, framerate) 
pipeline.start(config)

frame_dimensions = (streamWidth, streamHeight)
colorwriter = cv2.VideoWriter(colorVideoLocation, cv2.VideoWriter_fourcc(*'mp4v'), framerate, frame_dimensions)
t0 = time.time()
counter = 0

try:
    while (time.time()-t0)<timeRecord:
        counter+=1
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()

        if not color_frame:
            continue

        color_image = np.asanyarray(color_frame.get_data())
        colorwriter.write(color_image)
finally:
    colorwriter.release()
    pipeline.stop()