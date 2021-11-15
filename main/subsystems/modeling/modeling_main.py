# library imports
import numpy as np
import cv2
import os
import time
import argparse

# relative imports
from toolbox.globals import MACHINE, PATHS, PARAMETERS, MODE, MODEL_COLORS, MODEL_LABELS, print

# import parameters from the info.yaml file
from subsystems.integration.import_parameters import *
should_use_tensor_rt = hardware_acceleration == 'tensor_rt'
should_use_gpu       = hardware_acceleration == 'gpu'

# enable certain imports if tensorRT is enabled to prevent crashes in case it is not enabled
if should_use_tensor_rt:
    import pycuda.autoinit  # This is needed for initializing CUDA driver
    from modeling.yolo_with_plugins import TrtYOLO

class ModelingClass:
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

    def filter_team(self,boxes,confidences,class_ids):
        """
        Filter bounding boxes based on team color.

        Input: All boxes, confidences, class_ids
        Output: Enemy boxes, confidences, and class_ids
        """
        enemy_boxes = []
        enemy_confidences = []
        enemy_class_ids = []

        for index in range(len(boxes)):
            if class_ids[index] != self.team_color:
                enemy_boxes.append(boxes[index])
                enemy_confidences.append(confidences[index])
                enemy_class_ids.append(class_ids[index])

        print(enemy_boxes)
        return enemy_boxes,enemy_confidences,enemy_class_ids

    def get_optimal_bounding_box(self, boxes, confidences, screen_center, distance):
        """
        Decide the single best bounding box to aim at using a score system.

        Input: All detected bounding boxes with their confidences and the screen_center location of the image.
        Output: Best bounding box and its confidence.
        """

        best_bounding_box = boxes[0]
        best_score = 0
        cf = 0
        normalization_constant = distance((screen_center[0]*2,screen_center[1]*2),(screen_center[0],screen_center[1])) # Find constant used to scale distance part of score to 1

        # Sequentially iterate through all bounding boxes
        for i in range(len(boxes)):
            bbox = boxes[i]
            score = (1 - distance(screen_center,(bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2))/ normalization_constant) + confidences[i] # Compute score using distance and confidence

            # Make current box the best if its score is the best so far
            if score > best_score:
                best_bounding_box = boxes[i]
                best_score = score
                cf = confidences[i]
        
        return best_bounding_box, cf

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
        class_ids = []

        if should_use_tensor_rt:
            boxes, confidences, class_ids = self.trtYolo.detect(frame, ithreshold)
            new_boxes = []
            new_confidences = []
            new_class_ids = []

            # Filter bounding boxes based on confidence
            for i in range(len(boxes)):
                if confidences[i] >= iconfidence:
                    box = boxes[i]
                    new_box = [box[0],box[1],abs(box[2]-box[0]),abs(box[3]-box[1])]
                    new_boxes.append(new_box)
                    new_confidences.append(confidences[i])
                    new_class_ids.append(class_ids[i])

            boxes = new_boxes
            confidences = new_confidences
            class_ids = new_class_ids
        else:
            if self.W is None or self.H is None:
                (self.H, self.W) = frame.shape[:2]

            # convert image to blob before running it in the model
            blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (self.input_dimension, self.input_dimension), swapRB=True, crop=False)
            
            # provide input and retrive output
            self.net.setInput(blob)
            layer_outputs = self.net.forward(self.output_layer_names)

            # loop over each of the layer outputs
            for output in layer_outputs:
                # loop over each of the detections
                for detection in output:
                    # extract the class ID and confidence (i.e., probability)
                    # of the current object detection
                    scores = detection[5:]
                    class_id = np.argmax(scores)
                    confidence = scores[class_id]

                    # filter out weak predictions by ensuring the detected
                    # probability is greater than the minimum probability
                    if confidence > iconfidence:
                        # scale the bounding box coordinates back relative to
                        # the size of the image, keeping in mind that YOLO
                        # actually returns the center (x, y)-coordinates of
                        # the bounding box followed by the boxes' width and
                        # height
                        box = detection[0:4] * np.array([self.W,self. H, self.W, self.H])
                        (center_x, center_y, width, height) = box.astype("int")

                        # use the center (x, y)-coordinates to derive the top
                        # and and left corner of the bounding box
                        x = int(center_x - (width / 2))
                        y = int(center_y - (height / 2))

                        # update our list of bounding box coordinates,
                        # confidences, and class IDs
                        boxes.append([x, y, int(width), int(height)])

                        confidences.append(float(confidence))
                        class_ids.append(class_id)

        return boxes, confidences, class_ids
        
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
        
        # Uncomment to draw bounding boxes around all robots
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
        
        # return boxes, confidences, class_ids, frame