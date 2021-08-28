import pyrealsense2.pyrealsense2 as rs
import numpy as np
import cv2
import datetime
import os

# relative imports
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print

stream_width = PARAMETERS['aiming']['stream_width']
stream_height = PARAMETERS['aiming']['stream_height']
framerate = PARAMETERS['aiming']['stream_framerate']
color_video_location = PATHS['record_video_output_color']

pipeline = rs.pipeline()                                            
config = rs.config()                                                
config.enable_stream(rs.stream.depth, stream_width, stream_height, rs.format.z16, framerate)  
config.enable_stream(rs.stream.color, stream_width, stream_height, rs.format.bgr8, framerate) 
pipeline.start(config)
video_output = None

try:
    # Setup video output path based on date and counter
    c=1
    file_path = color_video_location.replace(".do_not_sync",datetime.datetime.now().strftime("%Y-%m-%d")+"_"+str(c)+".do_not_sync")
    while os.path.isfile(file_path):
        c+=1
        file_path = color_video_location.replace(".do_not_sync",datetime.datetime.now().strftime("%Y-%m-%d")+"_"+str(c)+".do_not_sync")

    # Start up video output
    gst_out = "appsrc ! video/x-raw, format=BGR ! queue ! videoconvert ! video/x-raw,format=BGRx ! nvvidconv ! nvv4l2h264enc ! h264parse ! matroskamux ! filesink location="+file_path
    video_output = cv2.VideoWriter(gst_out, cv2.CAP_GSTREAMER, 0, float(framerate), (int(stream_width), int(stream_height)))
    if not video_output.isOpened():
        print("Failed to open output")
    else:
        while True:
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()

            if not color_frame:
                continue

            color_image = np.asanyarray(color_frame.get_data())
            video_output.write(color_image)
            print("Writing")
finally:
    print("Finished")
    video_output.release()
    pipeline.stop()