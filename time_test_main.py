# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 19:43:04 2020

@author: xyf11
"""
import numpy as np
import tracker
import cv2
import os
import yolo_video_timetest

def main():
    # 
    # 
    # Configuration 
    # 
    # 
    inputpath = "test.avi"
    output = "output.avi"
    yolo = "./v3t1k/"
    confidence = 0.5
    threshold = 0.3
    weights_fname='v3t.weights'
    cfg_fname='v3t.cfg'
    classes_fname='v3t.names'

    # construct the argument parse and parse the arguments

    # load the COCO class labels our YOLO model was trained on
    labelsPath = os.path.sep.join([yolo, classes_fname])
    LABELS = open(labelsPath).read().strip().split("\n")

    # initialize a list of colors to represent each possible class label
    np.random.seed(42)
    COLORS = np.random.randint(0, 255, size=(len(LABELS), 3), dtype="uint8")

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

    counter = 0
    
    # 
    # 
    # main loop
    # 
    # 
    while True:
        grabbed, frame = vs.read()

        if counter % 100 == 0:
            # call model
            boxes = yolo_video_timetest.model(frame,net,yolo,confidence,threshold)
            tracker.init(frame,boxes)
        else:
            # call tracker
            frame = tracker.draw(frame)
            cv2.imshow('frame',frame)

        # wait for each keyframe
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        # read the next frame from the file
        counter += 1

if __name__ == '__main__':
    main()
