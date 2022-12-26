# library imports
import numpy as np
import cv2
import os
import time
from super_map import LazyDict

# project imports
from toolbox.globals import path_to, absolute_path_to, config, print, runtime
from toolbox.geometry_tools import BoundingBox, Position

# 
# config
# 
hardware_acceleration         = config.model.hardware_acceleration
input_dimension               = config.model.input_dimension
which_model                   = config.model.which_model
load_from_pickle              = config.model.load_from_pickle

# config check
assert hardware_acceleration in ['tensor_rt', 'gpu', None]

# 
# 
# helpers
# 
# 
def init_yolo_v7(model):
    print("\n[modeling] YOLO v7 loading")
    yolo_model   = None
    normal_model = None
        
    # 
    # tensor_rt
    # 
    if hardware_acceleration == 'tensor_rt':
        print("[modeling]     tensor_rt: ENABLED\n")
        import pycuda.autoinit  # This is needed for initializing CUDA driver
        try:
            import ctypes
            ctypes.cdll.LoadLibrary(absolute_path_to.tensorrt_so_file)
        except OSError as error:
            raise SystemExit(f'ERROR: failed to load {absolute_path_to.tensorrt_so_file}  Did you forget to do a "make" in the "./plugins/" subdirectory?') from error
        
        from subsystems.modeling.yolo_with_plugins import TrtYOLO
        
        yolo_model = TrtYOLO(
            path_to_model=path_to.yolo_v7.tensor_rt_file,
            input_shape=(input_dimension, input_dimension),
            category_num=3, # what is the 3? -- Jeff
            letter_box=False
        )
    # 
    # gpu
    # 
    elif hardware_acceleration == 'gpu':
        # FIXME
    # 
    # cpu
    # 
    else:
        # FIXME
        pass
    
    # 
    # export data
    # 
    model.trt_yolo           = yolo_model
    model.net                = normal_model
    model.get_bounding_boxes = lambda *args, **kwargs: yolo_v7_bounding_boxes(model, *args, **kwargs)

def yolo_v7_bounding_boxes(model, frame, minimum_confidence, threshold):
    # NOTE: this code is derived from https://www.pyimagesearch.com/2018/11/12/yolo-object-detection-with-opencv/

    # initialize our lists of detected bounding boxes, confidences, and class IDs, respectively
    boxes       = []
    confidences = []
    class_ids   = []

    if hardware_acceleration == 'tensor_rt':
        boxes, confidences, class_ids = model.trt_yolo.detect(frame, threshold)
        new_boxes = []
        new_confidences = []
        new_class_ids = []

        # filter bounding boxes based on minimum_confidence
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
        
        labels = []
        try:
            layer_outputs = model.net(frame)
            labels = layer_outputs.xyxy[0]
        except Exception as error:
            print(error)

        # loop over each of the detections
        if not isinstance(labels, list):
            labels = labels.cpu()
        for detection in labels:
            x_top_left, y_top_left, x_bottom_right, y_bottom_right, box_confidence, class_id = detection

            # filter out weak predictions
            if box_confidence > minimum_confidence:
                boxes.append(
                    BoundingBox.from_points(
                        top_left=(x_top_left, y_top_left),
                        bottom_right=(x_bottom_right, y_bottom_right),
                    )
                )
                confidences.append(float(box_confidence))
                class_ids.append(class_id)
    
    return boxes, confidences, class_ids