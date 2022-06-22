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
should_use_tensor_rt = config.model.hardware_acceleration == 'tensor_rt'
should_use_gpu       = config.model.hardware_acceleration == 'gpu'
input_dimension      = config.model.input_dimension
# config check
assert config.model.hardware_acceleration in ['tensor_rt', 'gpu', None]

# 
# shared data (imported by modeling and integration)
# 
runtime.modeling = LazyDict(
    boxes=[],
    confidences=[],
    best_bounding_box=[],
    current_confidence=0,
    found_robot=False,
)

# 
# 
# load model
# 
# 
model = LazyDict()
print("[INFO] loading YOLO from disk...")
# Setup modeling system based on forms of gpu acceleration
if should_use_tensor_rt: # tensorRT enabled
    import pycuda.autoinit  # This is needed for initializing CUDA driver
    from subsystems.modeling.yolo_with_plugins import TrtYOLO
    print("RUNNING WITH TENSORRT")
    model.trt_yolo = TrtYOLO(input_shape=(input_dimension, input_dimension), category_num=3, letter_box=False) # what is the 3? -- Jeff
else:
    model.net = cv2.dnn.readNetFromDarknet(path_to.model_config, path_to.model_weights)  # init the model
    if should_use_gpu:
        print("RUNNING WITH GPU ACCELERATION")
        model.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
        model.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
    else:
        print("RUNNING WITHOUT GPU ACCELERATION")
    model.layer_names = model.net.getLayerNames()
    model.output_layer_names = [model.layer_names[index[0] - 1] for index in model.net.getUnconnectedOutLayers()]
    model.W, model.H = None, None


# 
# 
# main function
# 
# 
def when_frame_arrives():
    # all boxes
    boxes, confidences, class_ids = get_bounding_boxes(
        frame=runtime.color_image,
        minimum_confidence=config.model.minimum_confidence,
        threshold=config.model.threshold,
    )
    
    screen_center = compute_screen_center(runtime.color_image)
    
    # best box
    best_bounding_box, current_confidence = get_optimal_bounding_box(
        boxes=boxes,
        confidences=confidences,
        screen_center=screen_center,
        distance=aiming.distance,
    )
    
    # export data
    runtime.screen_center               = screen_center
    runtime.modeling.boxes              = boxes
    runtime.modeling.confidences        = confidences
    runtime.modeling.best_bounding_box  = best_bounding_box
    runtime.modeling.current_confidence = current_confidence
    runtime.modeling.found_robot        = best_bounding_box is not None

# 
# 
# helpers
# 
# 
def compute_screen_center(color_image):
    return (color_image.shape[1] / 2, color_image.shape[0] / 2)

def get_bounding_boxes(frame, minimum_confidence, threshold):
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
                current_confidence = scores[class_id]

                # filter out weak predictions by ensuring the detected
                # probability is greater than the minimum probability
                if current_confidence > minimum_confidence:
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

                    confidences.append(float(current_confidence))
                    class_ids.append(class_id)
       
    if config.filter_team_color:
        boxes, confidences, class_ids = filter_team(boxes, confidences, class_ids)
    
    # 
    # share data
    # 
    return boxes, confidences, class_ids
    

def get_optimal_bounding_box(boxes, confidences, screen_center, distance):
    """
    Decide the single best bounding box to aim at using a score system.

    Input: All detected bounding boxes with their confidences and the screen_center location of the image.
    Output: Best bounding box and its confidence.
    """
    # no boxes
    if len(boxes) == 0:
        return None, 1
    
    best_bounding_box = boxes[0]
    best_score = 0
    confidence = 0
    normalization_constant = distance((screen_center[0]*2,screen_center[1]*2),(screen_center[0],screen_center[1])) # Find constant used to scale distance part of score to 1

    # Sequentially iterate through all bounding boxes
    for i in range(len(boxes)):
        bbox = boxes[i]
        score = (1 - distance(screen_center,(bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2))/ normalization_constant) + confidences[i] # Compute score using distance and confidence

        # Make current box the best if its score is the best so far
        if score > best_score:
            best_bounding_box = boxes[i]
            best_score = score
            confidence = confidences[i]
    
    return best_bounding_box, confidence


color_to_class_id = dict(
    red=0,
    blue=1,
)
def filter_team(boxes, confidences, class_ids):
    """
    Filter bounding boxes based on team color.

    Input: All boxes, confidences, class_ids
    Output: Enemy boxes, confidences, and class_ids
    """
    enemy_boxes = []
    enemy_confidences = []
    enemy_class_ids = []
    
    for index in range(len(boxes)):
        if class_ids[index] != color_to_class_id[config.our_team_color]:
            enemy_boxes.append(boxes[index])
            enemy_confidences.append(confidences[index])
            enemy_class_ids.append(class_ids[index])

    print(enemy_boxes, end=", ")
    return enemy_boxes,enemy_confidences,enemy_class_ids