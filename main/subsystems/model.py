# library imports
import numpy as np
import cv2
import os
import time
from super_map import LazyDict

# project imports
from toolbox.globals import path_to, config, print, runtime
from toolbox.geometry_tools import BoundingBox, Position
from toolbox.image_tools import Image
import subsystems.aim as aiming

# 
# config
# 
our_team_color        = config.our_team_color
hardware_acceleration = config.model.hardware_acceleration
input_dimension       = config.model.input_dimension
which_model           = config.model.which_model
hue_shift_amount      = config.model.hue_shift_amount

# config check
assert hardware_acceleration in ['tensor_rt', 'gpu', None]

# 
# shared data (imported by aiming and integration)
# 
runtime.modeling = LazyDict(
    bounding_boxes=[],
    enemy_boxes=[],
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
model = LazyDict(
    W=None,
    H=None,
)

if which_model == 'yolo_v4':
    from subsystems.modeling.yolo_v4 import init_yolo_v4
    init_yolo_v4(model)
elif which_model == 'yolo_v5':
    from subsystems.modeling.yolo_v5 import init_yolo_v5
    init_yolo_v5(model)
elif which_model == 'yolo_v7':
    from subsystems.modeling.yolo_v7 import init_yolo_v7
    init_yolo_v7(model)
else:
    raise Exception("Model specified under /'model.which_model/' is not supported")

# 
# 
# main function
# 
# 
def when_frame_arrives():
    if our_team_color == 'red':
        # change all the blue panels to red with hue shifting
        frame = Image(runtime.color_image).shift_hue(hue_shift_amount).in_cv2_format
    elif our_team_color == 'blue':
        frame = runtime.color_image # we don't need to modify the image
    else:
        raise Exception(f''' our_team_color:{our_team_color} which was not red or blue''')
    
    # 
    # all boxes
    # 
    all_boxes, confidences, class_ids = model.get_bounding_boxes(
        frame=frame,
        minimum_confidence=config.model.minimum_confidence,
        threshold=config.model.threshold,
    )
    screen_center = compute_screen_center(runtime.color_image)
    
    # 
    # remove our-team
    # 
    if config.filter_team_color:
        enemy_boxes, confidences, class_ids = filter_team(list(all_boxes), confidences, class_ids)
    
    # best box
    best_bounding_box, current_confidence = get_optimal_bounding_box(
        boxes=enemy_boxes,
        confidences=confidences,
        screen_center=screen_center,
        distance=aiming.distance,
    )
    
    # export data
    runtime.screen_center               = screen_center
    runtime.modeling.bounding_boxes     = all_boxes
    runtime.modeling.enemy_boxes        = enemy_boxes
    runtime.modeling.confidences        = confidences
    runtime.modeling.best_bounding_box  = best_bounding_box
    runtime.modeling.current_confidence = current_confidence
    runtime.modeling.found_robot        = best_bounding_box is not None

# 
# 
# helpers
# 
# 
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


if which_model == 'yolo_v5':
    color_to_class_id = dict(
        blue=0,
        red=1,
    )
else:
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
        if class_ids[index] != color_to_class_id['blue']: # always shoot at red, we use hue shifting to make blue things red
            enemy_boxes.append(boxes[index])
            enemy_confidences.append(confidences[index])
            enemy_class_ids.append(class_ids[index])

    return enemy_boxes, enemy_confidences, enemy_class_ids

def compute_screen_center(color_image):
    return (color_image.shape[1] / 2, color_image.shape[0] / 2)