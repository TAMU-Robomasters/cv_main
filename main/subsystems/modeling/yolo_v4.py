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
def init_yolo_v4(model):
    print("[modeling] YOLO v4 loading")
    trt_yolo           = None
    net                = None
    layer_names        = None
    output_layer_names = None
    
    # 
    # tensor_rt
    # 
    if hardware_acceleration == 'tensor_rt':
        print("[modeling]     tensor_rt: ENABLED\n")
        import pycuda.autoinit  # This is needed for initializing CUDA driver
        from subsystems.modeling.yolo_with_plugins import TrtYOLO
        trt_yolo = TrtYOLO(
            path_to_model=path_to.yolo_v4.tensor_rt_file,
            input_shape=(input_dimension, input_dimension),
            category_num=3, # what is the 3? -- Jeff
            letter_box=False
        )
    # 
    # gpu
    # 
    elif hardware_acceleration == 'gpu':
        print("[modeling]     gpu: ENABLED\n")
        net = cv2.dnn.readNetFromDarknet(path_to.yolo_v4.model_config, path_to.yolo_v4.model_weights)  # init the model
        net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
        layer_names = net.getLayerNames()
        output_layer_names = [layer_names[index[0] - 1] for index in net.getUnconnectedOutLayers()]
    # 
    # cpu
    # 
    else:
        print("[modeling]     falling back on CPU")
        net = cv2.dnn.readNetFromDarknet(path_to.yolo_v4.model_config, path_to.yolo_v4.model_weights)  # init the model
        layer_names = net.getLayerNames()
        output_layer_names = [layer_names[index[0] - 1] for index in net.getUnconnectedOutLayers()]
    
    # export data
    model.trt_yolo           = trt_yolo
    model.net                = net
    model.layer_names        = layer_names
    model.output_layer_names = output_layer_names
    model.get_bounding_boxes = lambda *args, **kwargs: yolo_v4_get_bounding_boxes(model, *args, **kwargs)
    
def yolo_v4_get_bounding_boxes(model, frame, minimum_confidence, threshold):
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
        
        # convert image to blob before running it in the model
        blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (input_dimension, input_dimension), swapRB=True, crop=False)
        # provide input and retrive output
        model.net.setInput(blob)
        layer_outputs = model.net.forward(model.output_layer_names)

        # loop over each of the layer outputs
        for output in layer_outputs:
            # loop over each of the detections
            for detection in output:
                # extract the class ID and minimum_confidence (i.e., probability)
                # of the current object detection
                scores = detection[5:]
                class_id = np.argmax(scores)
                this_confidence = scores[class_id]

                # filter out weak predictions by ensuring the detected
                # probability is greater than the minimum probability
                if this_confidence > minimum_confidence:
                    # scale the bounding box coordinates back relative to
                    # the size of the image, keeping in mind that YOLO
                    # actually returns the center (x, y)-coordinates of
                    # the bounding box followed by the boxes' width and
                    # height
                    box = detection[0:4] * np.array([model.W,model.H, model.W, model.H])
                    (center_x, center_y, width, height) = box.astype("int")

                    # use the center (x, y)-coordinates to derive the top
                    # and and left corner of the bounding box
                    x = int(center_x - (width / 2))
                    y = int(center_y - (height / 2))

                    # update our list of bounding box coordinates,
                    # confidences, and class IDs
                    boxes.append([x, y, int(width), int(height)])

                    confidences.append(float(this_confidence))
                    class_ids.append(class_id)
       
    # 
    # share data
    # 
    return boxes, confidences, class_ids
    

