from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, COLOR_GREEN, print
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

    def __init__(self, input_source,debug_mode=False):
        super(VideoStream, self).__init__()
        self.input_source=input_source
        self.frame=None
        self.debug_mode=debug_mode

    def run(self):
        """
        Continuously read and save current input from camera
        """
        cam=cv2.VideoCapture(self.input_source)
        while True:
            # Wait for a coherent pair of frames: depth and color
            ok, frame = cam.read()
            self.frame=frame
            print(self.frame.shape)
            
            cv2.waitKey(1)
            if self.debug_mode:
                current_time = time.time()
                print('FPS: ', 1 / (current_time - last_time))
                last_time = current_time

    def get_frames(self):
        return self.frame


def get_latest_frame():
    # FIXME: test/integrate a synchronous way to get frames from camera/embedded
    # OR change the way main works so that it doesn't need synchronous
    raise Exception('Synchronous get latest frame not yet implemented')