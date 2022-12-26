# library imports
import numpy as np
import cv2
import os
import time
from super_map import LazyDict
import torch

# project imports
from toolbox.globals import path_to, absolute_path_to, config, print, runtime
from toolbox.geometry_tools import BoundingBox, Position

# 
# config
# 
hardware_acceleration         = config.model.hardware_acceleration
input_dimension               = config.model.input_dimension
which_model                   = config.model.which_model

# config check
assert hardware_acceleration in ['tensor_rt', 'gpu', None]

# 
# 
# helpers
# 
# 
def init_yolo_v7(model):
    print("\n[modeling] YOLO v7 loading")
    loaded_model = None

    if hardware_acceleration == 'tensor_rt':
        print("[modeling]   tensor_rt: ENABLED\n")
    else:
        if not os.path.exists(path_to.yolo_v7.path_to_folder):
            raise Exception(f"yolov7 repo not found at {path_to.yolo_v7.path_to_folder}")
        elif not os.path.exists(path_to.yolo_v7.pytorch_model):
            raise Exception(f"model not found at {path_to.yolo_v7.pytorch_model}")

        # load model locally
        loaded_model = torch.hub.load(path_to.yolo_v7.path_to_folder, 'custom', path_to.yolo_v7.pytorch_model, source='local')

        if hardware_acceleration == 'gpu' and torch.cuda.is_available():
            print(torch.cuda.is_available())
            print("[modeling]   gpu_acceleration: ENABLED\n")
            # loaded_model = loaded_model.to(torch.device("cuda"))
        else:
            print("[modeling]   Running on CPU\n")

        loaded_model.zero_grad(set_to_none=True)
        loaded_model.eval()
        torch.no_grad()
        
    # 
    # export data
    # 
    model.net                = loaded_model
    model.get_bounding_boxes = lambda *args, **kwargs: yolo_v7_bounding_boxes(model, *args, **kwargs)

def yolo_v7_bounding_boxes(model, frame, minimum_confidence, threshold):
    # NOTE: this code is derived from https://www.pyimagesearch.com/2018/11/12/yolo-object-detection-with-opencv/

    # initialize our lists of detected bounding boxes, confidences, and class IDs, respectively
    boxes       = []
    confidences = []
    class_ids   = []
    
    if model.W is None or model.H is None:
        (model.H, model.W) = frame.shape[:2]
    
    labels = []
    try:
        layer_outputs = model.net(frame)
        labels = layer_outputs.xyxy[0]
    except Exception as error:
        print(error)

    # # loop over each of the detections
    # if not isinstance(labels, list):
    #     labels = labels.cpu()
    # for detection in labels:
    #     x_top_left, y_top_left, x_bottom_right, y_bottom_right, box_confidence, class_id = detection

    #     # filter out weak predictions
    #     if box_confidence > minimum_confidence:
    #         boxes.append(
    #             BoundingBox.from_points(
    #                 top_left=(x_top_left, y_top_left),
    #                 bottom_right=(x_bottom_right, y_bottom_right),
    #             )
    #         )
    #         confidences.append(float(box_confidence))
    #         class_ids.append(class_id)
    
    return boxes, confidences, class_ids