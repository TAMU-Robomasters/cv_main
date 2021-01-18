import numpy as np
import cv2
import os
import time
import argparse
import cv2
import pycuda.autoinit  # This is needed for initializing CUDA driver

from source.modeling.yolo_with_plugins import TrtYOLO
# relative imports
from toolbox.globals import ENVIRONMENT,PATHS,PARAMETERS,MODE,MODEL_COLORS,MODEL_LABELS, print

class modelingClass:
    def __init__(self):
        self.input_dimension = PARAMETERS['model']['input_dimension']
        print("[INFO] loading YOLO from disk...")
        self.trtYolo = TrtYOLO((self.input_dimension, self.input_dimension), 3, False)
    
    def original_get_bounding_boxes(self,frame, iconfidence, ithreshold):
        """
        ex: boxes, confidences, class_ids = get_bounding_boxes(frame, 0.5, 0.3)
        
        @frame: should be an cv2 image (basically a numpy array)
        @iconfidence: should be a value between 0-1
        @ithreshold: should be a value between 0-1
        -
        @@returns:
        - a tuple containing
            - a list of bounding boxes, each formatted as (x, y, width, height)
            - a list of confidences
            - a list of class_ids
        NOTE: this code is derived from https://www.pyimagesearch.com/2018/11/12/yolo-object-detection-with-opencv/
        """
    

        # convert image to blob before running it in the model
        boxes, confidences, classIDs = self.trtYolo.detect(frame, ithreshold)
        newBoxes = []
        for box in boxes:
            newBox = [box[0],box[1],abs(box[2]-box[0]),abs(box[3]-box[1])]
            newBoxes.append(newBox)
        boxes = newBoxes
        return boxes, confidences, classIDs
        
    def get_bounding_boxes(self,frame, iconfidence, ithreshold):
        """	
        this function is the debugging counterpart to the actual get_bounding_boxes()	
            
        @frame: should be an cv2 image (basically a numpy array)	
        @iconfidence: should be a value between 0-1	
        @ithreshold: should be a value between 0-1	
        -	
        @@returns:	
        - a tuple containing	
            - a list of bounding boxes, each formatted as (x, y, width, height)	
            - a list of confidences	
            - a list of class_ids	
        """

        # 	
        # wrap the original, but display every frame	
        # 
        boxes, confidences, class_ids = self.original_get_bounding_boxes(frame, iconfidence, ithreshold)

        # if MODE == "production":
        #     return boxes, confidences, class_ids
        # # apply non-maxima suppression to suppress weak, overlapping
        # # bounding boxes
        # idxs = cv2.dnn.NMSBoxes(boxes, confidences, iconfidence, ithreshold)
        
        # # ensure at least one detection exists
        # if len(idxs) > 0:
        #     # loop over the indexes we are keeping
        #     for i in idxs.flatten():
        #         # extract the bounding box coordinates

        #         (x, y) = (boxes[i][0], boxes[i][1])
        #         (w, h) = (boxes[i][2], boxes[i][3])
        #         # draw a bounding box rectangle and label on the frame
        #         color = [int(c) for c in MODEL_COLORS[class_ids[i]]]
        #         cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        #         text = "{}: {:.4f}".format(MODEL_LABELS[class_ids[i]],confidences[i])
        #         cv2.putText(frame, text, (x, y - 5),cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        return boxes, confidences, class_ids,frame