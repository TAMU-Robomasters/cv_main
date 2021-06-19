# library imports
import numpy as np
import cv2
import os
import time
import argparse

# relative imports
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, MODE, MODEL_COLORS, MODEL_LABELS, print

# import parameters from the info.yaml file
hardware_acceleration = PARAMETERS['model']['hardware_acceleration']
should_use_tensor_rt = hardware_acceleration == 'tensor_rt'
should_use_gpu       = hardware_acceleration == 'gpu'

# enable certain imports if tensorRT is enabled to prevent crashes in case it is not enabled
if should_use_tensor_rt:
    import pycuda.autoinit  # This is needed for initializing CUDA driver
    from source.modeling.yolo_with_plugins import TrtYOLO

class modelingClass:
    def __init__(self,team_color):
        self.input_dimension = PARAMETERS['model']['input_dimension']
        print("[INFO] loading YOLO from disk...")
        self.team_color = team_color
        # Setup modeling system based on forms of gpu acceleration
        if should_use_tensor_rt: # tensorRT enabled
            print("RUNNING WITH TENSORRT")
            self.trtYolo = TrtYOLO((self.input_dimension, self.input_dimension), 3, False)
        else:
            self.net = cv2.dnn.readNetFromDarknet(PATHS["model_config"], PATHS["model_weights"])  # init the model
            if should_use_gpu:
                print("RUNNING WITH GPU ACCELERATION")
                self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
                self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
            else:
                print("RUNNING WITHOUT GPU ACCELERATION")
            self.layer_names = self.net.getLayerNames()
            self.output_layer_names = [self.layer_names[index[0] - 1] for index in self.net.getUnconnectedOutLayers()]
            self.W, self.H = None, None

    def filter_team(self,boxes,confidences,classIDs):
        """
        Filter bounding boxes based on team color.

        Input: All boxes, confidences, classIDs
        Output: Enemy boxes, confidences, and classIDs
        """
        enemyBoxes = []
        enemyConfidences = []
        enemyClassIDs = []

        for index in range(len(boxes)):
            if classIDs[index] != self.team_color:
                enemyBoxes.append(boxes[index])
                enemyConfidences.append(confidences[index])
                enemyClassIDs.append(classIDs[index])

        print(enemyBoxes)
        return enemyBoxes,enemyConfidences,enemyClassIDs

    def original_get_bounding_boxes(self,frame, iconfidence, ithreshold):
        """
        ex: boxes, confidences, class_ids = get_bounding_boxes(frame, 0.5, 0.3)
        
        @frame: should be an cv2 image (basically a numpy array)
        @iconfidence: should be a value between 0-1
        @ithreshold: should be a value between 0-1
        -
        @@returns:
        - a tuple containing
            - a list of bounding boxes, each formatted as (x, y, width, height) with (0,0) as bottom right of image
            - a list of confidences
            - a list of class_ids
        NOTE: this code is derived from https://www.pyimagesearch.com/2018/11/12/yolo-object-detection-with-opencv/
        """
        # initialize our lists of detected bounding boxes, confidences, and class IDs, respectively
        boxes = []
        confidences = []
        classIDs = []

        if should_use_tensor_rt:
            boxes, confidences, classIDs = self.trtYolo.detect(frame, ithreshold)
            newBoxes = []
            newConfidences = []
            newClassIDs = []

            # Filter bounding boxes based on confidence
            for i in range(len(boxes)):
                if confidences[i] >= iconfidence:
                    box = boxes[i]
                    newBox = [box[0],box[1],abs(box[2]-box[0]),abs(box[3]-box[1])]
                    newBoxes.append(newBox)
                    newConfidences.append(confidences[i])
                    newClassIDs.append(classIDs[i])

            boxes = newBoxes
            confidences = newConfidences
            classIDs = newClassIDs
        else:
            if self.W is None or self.H is None:
                (self.H, self.W) = frame.shape[:2]

            # convert image to blob before running it in the model
            blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (self.input_dimension, self.input_dimension), swapRB=True, crop=False)
            
            # provide input and retrive output
            self.net.setInput(blob)
            layerOutputs = self.net.forward(self.output_layer_names)

            # loop over each of the layer outputs
            for output in layerOutputs:
                # loop over each of the detections
                for detection in output:
                    # extract the class ID and confidence (i.e., probability)
                    # of the current object detection
                    scores = detection[5:]
                    classID = np.argmax(scores)
                    confidence = scores[classID]

                    # filter out weak predictions by ensuring the detected
                    # probability is greater than the minimum probability
                    if confidence > iconfidence:
                        # scale the bounding box coordinates back relative to
                        # the size of the image, keeping in mind that YOLO
                        # actually returns the center (x, y)-coordinates of
                        # the bounding box followed by the boxes' width and
                        # height
                        box = detection[0:4] * np.array([self.W,self. H, self.W, self.H])
                        (centerX, centerY, width, height) = box.astype("int")

                        # use the center (x, y)-coordinates to derive the top
                        # and and left corner of the bounding box
                        x = int(centerX - (width / 2))
                        y = int(centerY - (height / 2))

                        # update our list of bounding box coordinates,
                        # confidences, and class IDs
                        boxes.append([x, y, int(width), int(height)])

                        confidences.append(float(confidence))
                        classIDs.append(classID)

        return boxes, confidences, classIDs
        
    def get_bounding_boxes(self,frame, iconfidence, ithreshold, filter_team_color):
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

        if filter_team_color:
            boxes, confidences, class_ids = self.filter_team(boxes, confidences, class_ids)

        # if MODE == "production":
        return boxes, confidences, class_ids, frame
        
        # if not hardware_acceleration:
        #     # apply non-maxima suppression to suppress weak, overlapping
        #     # bounding boxes
        #     idxs = cv2.dnn.NMSBoxes(boxes, confidences, iconfidence, ithreshold)
            
        #     # ensure at least one detection exists
        #     if len(idxs) > 0:
        #         # loop over the indexes we are keeping
        #         for i in idxs.flatten():
        #             # extract the bounding box coordinates

        #             (x, y) = (boxes[i][0], boxes[i][1])
        #             (w, h) = (boxes[i][2], boxes[i][3])
        #             # draw a bounding box rectangle and label on the frame
        #             color = [int(c) for c in MODEL_COLORS[class_ids[i]]]
        #             cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        #             text = "{}: {:.4f}".format(MODEL_LABELS[class_ids[i]],confidences[i])
        #             cv2.putText(frame, text, (x, y - 5),cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # return boxes, confidences, class_ids, frame