import pyrealsense2 as rs
import numpy as np
import cv2
import pdb,time

# parameters
SHOW_IMAGES = False

# Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 60)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 60)
profile=pipeline.start(config)
depth_scale = profile.get_device().first_depth_sensor().get_depth_scale()
print(depth_scale)

# Start streaming
try:
    while True:
        start_t = time.time()
        # Wait for a coherent pair of frames: depth and color
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        align = rs.align(rs.stream.color)
        frames = align.process(frames)

        depth_frame = frames.get_depth_frame()
        if depth_frame and color_frame:
            print('ok')

        # Convert images to numpy arrays
        depth_image = np.asanyarray(depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())
        cv2.rectangle(color_image,(100,100,100,100),(255,0,0),2)
        cv2.imshow('d', depth_image)

        distance=(cv2.mean(depth_image[100:200,100:200].astype(float))[0]*depth_scale)
        # Apply colormap on depth image (image must be converted to 8-bit per pixel first)
        depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
        # Stack both images horizontally
        images = np.hstack((color_image, depth_colormap))

        # Show images
        if SHOW_IMAGES:
            cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)

        cv2.imshow('RealSense', images)
        cv2.waitKey(1)
        print('dist: ',distance,'time: ', 1/(time.time()-start_t))

finally:
    # Stop streaming
    pipeline.stop()