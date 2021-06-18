import pyrealsense2.pyrealsense2 as rs
import numpy as np
import cv2
import time

# relative imports
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

t0 = 0

try:
    # Setup video output path based on date and counter
    c=1
    filePath = colorVideoLocation.replace(".dont-sync",datetime.datetime.now().strftime("%Y-%m-%d")+"_"+str(c)+".dont-sync")
    while os.path.isfile(filePath):
        c+=1
        filePath = colorVideoLocation.replace(".dont-sync",datetime.datetime.now().strftime("%Y-%m-%d")+"_"+str(c)+".dont-sync")

    # Start up video output
    gst_out = "appsrc ! video/x-raw, format=BGR ! queue ! videoconvert ! video/x-raw,format=BGRx ! nvvidconv ! nvv4l2h264enc ! h264parse ! matroskamux ! filesink location="+filePath
    videoOutput = cv2.VideoWriter(gst_out, cv2.CAP_GSTREAMER, 0, float(framerate), (int(streamWidth), int(streamHeight)))
    if not videoOutput.isOpened():
        print("Failed to open output")

        while (time.time()-t0)<timeRecord:
            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()

            if not color_frame:
                continue

            color_image = np.asanyarray(color_frame.get_data())
            videoOutput.write(color_image)
finally:
    videoOutput.release()
    pipeline.stop()