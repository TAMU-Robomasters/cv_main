import math
import collections
from time import time as now

import numpy as np
from super_map import LazyDict
from statistics import mean as average

from toolbox.globals import path_to, config, print, runtime
from toolbox.geometry_tools import Position, BoundingBox
from subsystems.aiming.predictor import Predictor

# 
# config
# 
bot                                  = config.bot
stream_width                         = config.aiming.stream_width
stream_height                        = config.aiming.stream_height
stream_framerate                     = config.aiming.stream_framerate
grid_size                            = config.aiming.grid_size
horizontal_fov                       = config.aiming.horizontal_fov
vertical_fov                         = config.aiming.vertical_fov
model_fps                            = config.aiming.model_fps
bullet_velocity                      = config.aiming.bullet_velocity
length_barrel                        = config.aiming.length_barrel
camera_gap                           = config.aiming.camera_gap
min_size_for_stdev                   = config.aiming.min_size_for_stdev
std_error_bound                      = config.aiming.std_error_bound
min_range                            = config.aiming.min_range
max_range                            = config.aiming.max_range
blue_light                           = config.aiming.blue_light
blue_dark                            = config.aiming.blue_dark
area_arrow_bound                     = config.aiming.area_arrow_bound
center_image_offset                  = config.aiming.center_image_offset
min_area                             = config.aiming.min_area
r_timer                              = config.aiming.r_timer
barrel_camera_gap                    = config.aiming.barrel_camera_gap
sec_till_lock_lost                   = config.aiming.sec_till_lock_lost
disable_bullet_drop                  = config.aiming.disable_bullet_drop
prediction_method                    = config.aiming.prediction_method
linear_tracking_confidence_threshold = config.aiming.linear_tracking_confidence_threshold
linear_buffer_size                   = config.aiming.linear_buffer_size
skip_allowance                       = config.aiming.skip_allowance
camera                               = config.hardware.camera
confidence_box_height                = config.aiming.confidence_box_height
confidence_box_width                 = config.aiming.confidence_box_width
bullet_drop                          = config.aiming.bullet_drop

# 
# init
# 
if prediction_method == 'kalman': from subsystems.aiming.filter import KalmanFilter
x_circular_buffer = collections.deque(maxlen=config.aiming.min_size_for_stdev)
y_circular_buffer = collections.deque(maxlen=config.aiming.min_size_for_stdev)

time_circular_buffer = collections.deque(maxlen=config.aiming.min_size_for_stdev)

# 
# shared data (imported by modeling and integration)
# 
runtime.aiming = LazyDict(
    should_shoot=False,
    should_look_around=False,
    last_target_time=0,
    horizontal_angle=0,
    vertical_angle=0,
    horizonal_stdev=0,
    vertical_stdev=0,
    depth_amount=0,
    pixel_diff=0,
    predictor=Predictor(linear_buffer_size),
    confidence_box=None,
    predictor_skip_count=0,
    kalman_filter=None,
)

# 
# 
# main
# 
# 
lookback_size = 5
last_boxes = []
def when_bounding_boxes_refresh():
    global last_boxes
    # import data
    found_robot       = runtime.modeling.found_robot
    best_bounding_box = runtime.modeling.best_bounding_box
    depth_image       = runtime.depth_image
    confidence        = runtime.modeling.current_confidence
    screen_center     = runtime.screen_center
    acceleration      = runtime.realsense.acceleration if camera == 'realsense' else None
    gyro              = runtime.realsense.gyro         if camera == 'realsense' else None
    
    horizontal_angle, vertical_angle, should_shoot, horizonal_stdev, vertical_stdev, depth_amount, pixel_diff = (0, 0, 0, 0, 0, 0, 0)
    center_point, bullet_drop_point, prediction_point = (None, Position([0,0]), None)
    current_time = now()
    point_to_aim_at = Position([0,0])
    
    # 
    # update core aiming data
    # 
    if found_robot:
        point_to_aim_at = best_bounding_box.center
        depth_amount = get_distance_from_array(depth_image, best_bounding_box) # Find depth from camera to robot
        depth_out_of_bounds = depth_amount < min_range or depth_amount > max_range
    center_point = Position(point_to_aim_at) # for displaying
    time_circular_buffer.append(current_time)
        

    # 
    # prediction
    # 
    prediction_point = Position(point_to_aim_at) # for displaying 
    
    # 
    # compute offset (decide how much movement we need)
    # 
    if found_robot:
        horizontal_angle, vertical_angle = angle_from_center(point_to_aim_at, screen_center)
        
    #
    # bullet drop
    #
    if not disable_bullet_drop and found_robot:
        try:
            depth_int = int(math.floor(depth_amount))
            if depth_int in bullet_drop:
                angle_adjustment = bullet_drop[depth_int]
            # else: # more than 5 meters
            if depth_amount > 5:
                angle_adjustment = -(depth_amount+48)/100 # negative is aiming higher
                print(f'''HERE''')
            
            print(f'''angle_adjustment = {angle_adjustment:.4f}''', end=" ")
            vertical_angle += angle_adjustment
        except Exception as error:
            print(error)
        
                
    # 
    # update circular buffers
    # 
    if not found_robot or depth_out_of_bounds:
        x_circular_buffer.clear()
        y_circular_buffer.clear()
    else:
        x_circular_buffer.append(point_to_aim_at[0])
        y_circular_buffer.append(point_to_aim_at[1])
        horizonal_stdev = np.std(x_circular_buffer)
        vertical_stdev = np.std(y_circular_buffer)
        
    # 
    # should_shoot
    # 
    if not found_robot: 
        should_shoot = False
        runtime.aiming.confidence_box = None
        last_boxes.append(0)
    else:
        width = runtime.color_image.shape[1]
        height = runtime.color_image.shape[0]
        # print(f"width {width}, height {height}")
        x_top_left = (width - (confidence_box_width*width))/2
        y_top_left = (height - (confidence_box_height*height))/2
        
        confidence_box = BoundingBox([
            x_top_left, 
            y_top_left,
            (width-(x_top_left*2)),
            (height-(y_top_left*2)) + 10,
        ])
        runtime.aiming.confidence_box = confidence_box
        should_shoot = confidence_box.contains(best_bounding_box.center)
        
        last_boxes.append(1)
        
    last_boxes = last_boxes[-lookback_size:]
    time_sum = sum(last_boxes)
    if time_sum:
        should_shoot = True
        
            
        

    # 
    # should_look_around
    # 
    if current_time - runtime.aiming.last_target_time < sec_till_lock_lost:
        should_look_around = False
    else:
        should_look_around = True
    if found_robot:
        runtime.aiming.last_target_time = current_time
    
    # 
    # update the shared data
    # 
    runtime.aiming.should_look_around = should_look_around
    runtime.aiming.should_shoot       = should_shoot
    runtime.aiming.horizontal_angle   = horizontal_angle
    runtime.aiming.vertical_angle     = vertical_angle
    runtime.aiming.horizonal_stdev    = horizonal_stdev
    runtime.aiming.vertical_stdev     = vertical_stdev
    runtime.aiming.depth_amount       = depth_amount
    runtime.aiming.pixel_diff         = pixel_diff
    runtime.aiming.center_point       = center_point
    runtime.aiming.bullet_drop_point  = bullet_drop_point
    runtime.aiming.prediction_point   = prediction_point

# 
# 
# helpers
# 
# 
def get_distance_from_array(depth_frame_array, bbox):
    """
    Determines the depth of a bounding box by choosing and filtering the depths of specific points in the bounding box.

    Input: Depth frame and bounding box.
    Output: Single depth value.
    """
    if depth_frame_array is None:
        return 1
    try:
        # this is used to add to the current_x and current_y so that we can get the different points in the 9x9 grid
        x_interval = bbox.width  / grid_size
        y_interval = bbox.height / grid_size
        # stores the x and y of the last point in the grid we got the distance from
        curr_x = 0
        curr_y = 0
        distances = np.array([])
        # double for loop to go through 2D array of 9x9 grid
        for _ in range(grid_size):
            curr_x += x_interval # add the interval you calculated to traverse through the 9x9 grid
            # print(curr_x)
            if bbox.x_top_left+curr_x >= len(depth_frame_array[0]):
                break
            for _ in range(grid_size):
                curr_y += y_interval # add the interval you calculated to traverse through the 9x9 grid
                # gets the distance of the point from the depth frame on the grid and appends to the array
                # print(curr_y)
                if bbox.y_top_left+curr_y >= len(depth_frame_array):
                    break
                    
                depth_y = int(bbox.y_top_left+curr_y)
                depth_x = int(bbox.x_top_left+curr_x)
                distances = np.append(
                    distances, 
                    depth_frame_array[depth_y][depth_x]  /  1000,
                )
            curr_y = 0
        
        distances = distances[distances!=0.0]   # removes all occurances of 0.0 (areas where there is not enough data return 0.0 as depth)
        median = np.median(distances)           # gets the median from the array
        std = np.std(distances)                 # gets the standard deviation from the array
        modified_distances = []                  # initializes a new array for removing outlier numbers
        # goes through distances array and adds any values that are less than X*standard deviations and ignores the rest
        for i in range(np.size(distances)):
            if abs(distances[i] - median) < 1.5 * std: # tune the standard deviation range for better results
                modified_distances = np.append(modified_distances,distances[i])

        distance = (np.mean(modified_distances)+np.median(modified_distances))/2
        return distance if (distance and distance>0 and distance<10) else 1
    except Exception as error:
        print(f'''[aiming:get_distance_from_array] error/warning = {error}''')
        return 1

def distance(point_1: tuple, point_2: tuple):
    """
    Returns the distance between two points.

    Input: Two points.
    Output: Distance in pixels.
    """

    distance = (sum((p1 - p2) ** 2.0 for p1, p2 in zip(point_1, point_2))) ** (1 / 2)
    return distance

def angle_from_center(point_to_aim_at, screen_center):
    """
    Returns the x and y angles between the screen_center of the image and the screen_center of a bounding box.

    We send screen_center instead of importing 
    from info.yaml since recorded video footage could be different resolutions.

    Input: Bounding box and camera screen_center.
    Output: Horizontal and vertical angle in radians.
    """

    x_bbox_center, y_bbox_center, x_cam_center, y_cam_center = point_to_aim_at[0], screen_center[1]*2-point_to_aim_at[1], screen_center[0], screen_center[1]

    horizontal_angle = ((x_bbox_center-x_cam_center)/x_cam_center)*(horizontal_fov/2)
    vertical_angle = ((y_bbox_center-y_cam_center)/y_cam_center)*(vertical_fov/2)

    # print("horizontal_angle:",f"{horizontal_angle:.4f}"," vertical_angle:", f"{vertical_angle:.4f}", end=", ")

    return math.radians(horizontal_angle),math.radians(vertical_angle)
