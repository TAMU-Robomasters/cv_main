# library imports
import numpy as np
import cv2
import os
import time
from super_map import LazyDict

# project imports
from toolbox.globals import path_to, config, print, runtime
import subsystems.aim as aiming

# 
# config
# 
hardware_acceleration = config.model.hardware_acceleration
input_dimension       = config.model.input_dimension
which_model           = config.model.which_model
# config check
assert hardware_acceleration in ['tensor_rt', 'gpu', None]

# 
# 
# helpers
# 
# 
def init_yolo_v5(model):
    print("[modeling] YOLO v5 loading")
    yolo_model   = None
    normal_model = None
        
    # 
    # tensor_rt
    # 
    if hardware_acceleration == 'tensor_rt':
        print("[modeling]     tensor_rt: ENABLED\n")
        import pycuda.autoinit  # This is needed for initializing CUDA driver
        from subsystems.modeling.yolo_with_plugins import TrtYOLO
        yolo_model = TrtYOLO(
            path_to_model=path_to.yolo_v5.tensor_rt_file,
            input_shape=(input_dimension, input_dimension),
            category_num=3, # what is the 3? -- Jeff
            letter_box=False
        )
    # 
    # gpu
    # 
    elif hardware_acceleration == 'gpu':
        print("[modeling]     gpu: ENABLED\n")
        import torch
        device = torch.device("cuda")
        normal_model = torch.hub.load('ultralytics/yolov5', 'custom', path=path_to.yolov5_pt)
        normal_model.eval()
        torch.no_grad()
    # 
    # cpu
    # 
    else:
        print("[modeling]     falling back on CPU\n")
        import torch
        device = torch.device("cpu")
        normal_model = torch.hub.load('ultralytics/yolov5', 'custom', path=path_to.yolov5_pt)
        normal_model.eval()
        torch.no_grad()
    
    # 
    # export data
    # 
    model.trt_yolo           = yolo_model
    model.net                = normal_model
    model.get_bounding_boxes = lambda *args, **kwargs: yolo_v5_bounding_boxes(model, *args, **kwargs)

def yolo_v5_bounding_boxes(model, frame, minimum_confidence, threshold):
    # NOTE: this code is derived from https://www.pyimagesearch.com/2018/11/12/yolo-object-detection-with-opencv/

    # initialize our lists of detected bounding boxes, confidences, and class IDs, respectively
    boxes       = []
    confidences = []
    class_ids   = []

    if should_use_tensor_rt:
        boxes, confidences, class_ids = model.trt_yolo.detect(frame, threshold)
        new_boxes = []
        new_confidences = []
        new_class_ids = []

        # Filter bounding boxes based on minimum_confidence
        for i in range(len(boxes)):
            if confidences[i] >= minimum_confidence:
                box = boxes[i]
                new_box = [box[0],box[1],abs(box[2]-box[0]),abs(box[3]-box[1])]
                new_boxes.append(new_box)
                new_confidences.append(confidences[i])
                new_class_ids.append(class_ids[i])

        boxes = new_boxes
        confidences = new_confidences
        class_ids = new_class_ids
    else:
        if model.W is None or model.H is None:
            (model.H, model.W) = frame.shape[:2]
        
        layer_outputs = model.net(frame)
        labels = layer_outputs.xyxy[0]
        print('labels - ', labels)

        # loop over each of the detections
        for detection in labels:
            detection = detection.numpy()
            # extract the class ID and minimum_confidence (i.e., probability)
            # of the current object detection
            scores = detection[5:]
            class_id = np.argmax(scores)
            this_confidence = scores[class_id]

            # filter out weak predictions by ensuring the detected
            # probability is greater than the minimum probability
            if this_confidence > minimum_confidence:
                # update our list of bounding box coordinates,
                # confidences, and class IDs
                boxes.append(detection[0:4])

                confidences.append(float(current_confidence))
                class_ids.append(class_id)
       
    return boxes, confidences, class_ids