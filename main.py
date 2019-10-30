from modules import *
video_stream=VideoStream(show_img_flag=False,debug_mode=False)
video_stream.start()


#Example:
import cv2
import time
time.sleep(3)

while True:
    color_image,depth_image=video_stream.get_frames()
    cv2.imshow('color_image',color_image)
    cv2.waitKey(1)