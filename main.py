from modules import *
video_stream=VideoStream(input_source=0,debug_mode=False)
video_stream.start()


#Example:
import cv2
import time

time.sleep(3)
while True:
    #color_image,depth_image=video_stream.get_frames()
    #color_image=video_stream.get_frames()
    cv2.imshow('color_image',video_stream.frame)
    cv2.waitKey(1)