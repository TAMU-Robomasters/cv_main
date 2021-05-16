import pyrealsense2 as rs
import numpy as np
import cv2

pipeline = rs.pipeline()                                            # declares and initializes the pipeline variable
config = rs.config()                                                # declares and initializes the config variable for the pipeline
config.enable_stream(rs.stream.depth, 848, 480, rs.format.z16, 60)  # this starts the depth stream and sets the size and format
config.enable_stream(rs.stream.color, 848, 480, rs.format.bgr8, 60) # this starts the color stream and set the size and format
profile = pipeline.start(config)

def DistanceInBox(bbox):

    try:

        while True: 

            frames = pipeline.wait_for_frames()     # gets all frames
            depth_frame = frames.get_depth_frame()  # gets the depth frame
            color_frame = frames.get_color_frame()  # gets the color frame 
            if not depth_frame or not color_frame:  # if there is no aligned_depth_frame or color_frame then leave the loop
                continue

            # we turn the depth and color frames into numpy arrays because we need to draw a rectangle and stack the two arrays
            depth_image = np.asanyarray(depth_frame.get_data()) 

            # causes 1FPS Drop
            return getDistFromArray(depth_image, bbox)     # gets the distance for the normal depth image

    finally:
        pipeline.stop()
    return 0