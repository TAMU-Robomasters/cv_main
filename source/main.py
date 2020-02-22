# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 19:43:04 2020

@author: xyf11
"""
import tracker
import cv2
import os
from itertools import count
from yolo_video import model

def main():
    #
    #
    # Configuration
    #
    #
    input_path = "test.avi"
    yolo = "./v3t1k/"
    weights_fname='v3t.weights'
    cfg_fname='v3t.cfg'
    classes_fname='v3t.names'
    confidence = 0.5
    threshold = 0.3

    # derive the paths to the YOLO weights and model configuration
    weights_path = os.path.sep.join([yolo, weights_fname])
    config_path = os.path.sep.join([yolo, cfg_fname])

    # load our YOLO object detector trained on COCO dataset (80 classes)
    # and determine only the *output* layer names that we need from YOLO
    print("[INFO] loading YOLO from disk...")
    net = cv2.dnn.readNetFromDarknet(config_path, weights_path)
    ln = net.getLayerNames()
    ln = [ ln[each_layer[0] - 1] for each_layer in net.getUnconnectedOutLayers() ]
    video_stream = cv2.VideoCapture(input_path)

    #
    #
    # main loop
    #
    #
    ok = True

    for counter in count(start=0, step=1): # counts up infinitely starting at 0

        grabbed, frame = video_stream.read()
        print("counter:", counter)

        if counter % 20 == 0 or not ok:
            #
            # call model
            #
            boxes = model(frame,net,yolo,confidence,threshold)
            ok = tracker.init(frame,boxes)
        else:
            #
            # call tracker
            #
            frame, ok = tracker.draw(frame)

            cv2.imshow('frame',frame)

        # wait for a keypress on each frame
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

if __name__ == '__main__':
    main()
