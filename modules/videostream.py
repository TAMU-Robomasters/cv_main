import pyrealsense2 as rs
import cv2
import numpy as np
import threading
import time
import pdb

supported_RGB_config = {
    1920: {1080: [6, 15, 30]},
    1280: {720: [6, 15, 30]},
    960: {540: [6, 15, 30, 60]},
    848: {480: [6, 15, 30, 60]},
    640: {480: [6, 15, 30, 60], 360: [6, 15, 30, 60]},
    424: {240: [6, 15, 30, 60]},
    320: {240: [6, 30, 60], 180: [6, 30, 60]}
}
supported_depth_config = {
    1280: {720: [6, 15, 30]},
    848: {480: [6, 15, 30, 60, 90]},
    640: {480: [6, 15, 30, 60, 90], 360: [6, 15, 30, 60, 90]},
    480: {270: [6, 15, 30, 60, 90]},
    424: {240: [6, 15, 30, 60, 90]}
}


class VideoStream(threading.Thread):
    """
    Read and save color and depth images from camera
    """

    def __init__(self, color_stream_width=848, color_stream_height=480, color_stream_fps=60, depth_stream_width=848,
                 depth_stream_height=480, depth_stream_fps=60, show_img_flag=False, debug_mode=False):
        """
        Initialize VideoStream.
        Please check supported configurations before setting up the camera.
        :param color_stream_width: Width of color image output. Suggested to be greater than or equal to
            depth_stream_width.
        :param color_stream_height: Height of color image output. Suggested to be greater than or equal to
            depth_stream_height.
        :param color_stream_fps: Maximum color stream fps. (With auto-exposure this fps cannot be guaranteed)
        :param depth_stream_width: Width of depth image output.
        :param depth_stream_height: Height of depth image output.
        :param depth_stream_fps: Maximum depth stream fps.
        :param show_img_flag: Whether VideoStream class displays images or not.
        :param debug_mode: Toggle debug mode.
        """
        assert color_stream_width >= depth_stream_width and color_stream_height >= depth_stream_height, \
            "It is suggested to have RGB stream larger than depth stream."
        assert color_stream_width in supported_RGB_config and color_stream_height \
               in supported_RGB_config[color_stream_width] and color_stream_fps \
               in supported_RGB_config[color_stream_width][color_stream_height], "Unsupported RGB Configuration"
        assert depth_stream_width in supported_depth_config and depth_stream_height \
               in supported_depth_config[depth_stream_width] and depth_stream_fps \
               in supported_depth_config[depth_stream_width][depth_stream_height], "Unsupported Depth Configuration"
        super(VideoStream, self).__init__()
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.config.enable_stream(rs.stream.depth, depth_stream_width, depth_stream_height, rs.format.z16,
                                  depth_stream_fps)
        self.config.enable_stream(rs.stream.color, color_stream_width, color_stream_height, rs.format.bgr8,
                                  color_stream_fps)
        self.show_img_flag = show_img_flag
        self.debug_mode = debug_mode
        self.frames = None
        self.align = rs.align(rs.stream.color)
        self.pipeline.start(self.config)

    def run(self):
        """
        Continuously read and save current input from camera
        """
        try:
            last_time = 0
            while True:
                # Wait for a coherent pair of frames: depth and color
                frames = self.pipeline.wait_for_frames()

                if frames.get_color_frame() and frames.get_depth_frame():
                    self.frames = self.align.process(frames)
                else:
                    continue

                if self.show_img_flag:
                    color_image, depth_image = self.get_frames()
                    depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
                    # Stack both images horizontally
                    images = np.hstack((color_image, depth_colormap))

                    # Show images
                    cv2.imshow('VideoStream Output', images)
                    cv2.waitKey(1)
                if self.debug_mode:
                    current_time = time.time()
                    print('FPS: ', 1 / (current_time - last_time))
                    last_time = current_time
        except Exception as e:
            print(e)
        finally:
            self.pipeline.stop()

    def get_frames(self):
        """
        Process and return color and depth frames.
        :return: a list containing color image and depth image in numpy array format.
        """
        if self.frames is not None:
            color_frame = self.frames.get_color_frame()
            depth_frame = self.frames.get_depth_frame()
            color_image = np.asanyarray(color_frame.get_data())
            depth_image = np.asanyarray(depth_frame.get_data())  # in 0.1mm
            return [color_image, depth_image]
        else:
            print('frames is empty')
            return None
