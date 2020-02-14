# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 19:43:04 2020

@author: xyf11
"""
import numpy as np
import tracker
import argparse
import time
import cv2
import os
from datetime import datetime
from PIL import Image
import yolo_video_timetest
#import model

def main():
    inputpath = "test.avi"
    output = "output.avi"
    yolo = "./v3t1k/"
    confidence = 0.5
    threshold = 0.3
    # yolo_video_timetest.modeling(inputpath,output,yolo,confidence,threshold)
    weights_fname='v3t.weights'
    cfg_fname='v3t.cfg'
    classes_fname='v3t.names'

    # construct the argument parse and parse the arguments
#    ap = argparse.ArgumentParser()
#    ap.add_argument("-i", "--input", required=True,
#    	help="path to input video")
#    ap.add_argument("-o", "--output", required=True,
#    	help="path to output video")
#    ap.add_argument("-y", "--yolo", required=True,
#    	help="base path to YOLO directory")
#    ap.add_argument("-c", "--confidence", type=float, default=0.5,
#    	help="minimum probability to filter weak detections")
#    ap.add_argument("-t", "--threshold", type=float, default=0.3,
#    	help="threshold when applyong non-maxima suppression")
#    args = vars(ap.parse_args())
#
    # load the COCO class labels our YOLO model was trained on
    labelsPath = os.path.sep.join([yolo, classes_fname])
    LABELS = open(labelsPath).read().strip().split("\n")

    # initialize a list of colors to represent each possible class label
    np.random.seed(42)
    COLORS = np.random.randint(0, 255, size=(len(LABELS), 3),
        dtype="uint8")

    # derive the paths to the YOLO weights and model configuration
    weightsPath = os.path.sep.join([yolo, weights_fname])
    configPath = os.path.sep.join([yolo, cfg_fname])

    # load our YOLO object detector trained on COCO dataset (80 classes)
    # and determine only the *output* layer names that we need from YOLO
    print("[INFO] loading YOLO from disk...")
    net = cv2.dnn.readNetFromDarknet(configPath, weightsPath)
    ln = net.getLayerNames()
    ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]

    # initialize the video stream, pointer to output video file, and
    # frame dimensions

    vs = cv2.VideoCapture(inputpath)

    writer = None
    (W, H) = (None, None)

    # try to determine the total number of frames in the video file
    # try:
    #     #prop = cv2.cv.CV_CAP_PROP_FRAME_COUNT if imutils.is_cv2() else cv2.CAP_PROP_FRAME_COUNT
    #     total = int(vs.get(cv2.CV_CAP_PROP_FRAME_COUNT))
    #     print("[INFO] {} total frames in video".format(total))
    #
    # # an error occurred while trying to determine the total
    # # number of frames in the video file
    # except:
    #     print("[INFO] could not determine # of frames in video")
    #     print("[INFO] no approx. completion time can be provided")
    #     total = -1

    counter = 0

    while True:
        grabbed, frame = vs.read()

        # to avoid overflow ?
        # if counter > 1000000:
        #     counter = 0

        if counter % 100 == 0:
            # call model
            boxes = yolo_video_timetest.model(frame,net,yolo,confidence,threshold)
            tracker.init(frame,boxes)
            print('asd')
        else:
            # call tracker
            # print(grabbed)
            frame = tracker.draw(frame)
            cv2.imshow('frame',frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # read the next frame from the file
        counter += 1

if __name__ == '__main__':
    main()

    #print(result)
