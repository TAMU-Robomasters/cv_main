import math
import collections
from time import time as now

import numpy as np
from super_map import LazyDict
from statistics import mean as average

from toolbox.globals import path_to, config, print, runtime
from toolbox.geometry_tools import Position

# 
# config
# 
prediction_time        = config.aiming.prediction_time
stream_width           = config.aiming.stream_width
stream_height          = config.aiming.stream_height
stream_framerate       = config.aiming.stream_framerate
grid_size              = config.aiming.grid_size
horizontal_fov         = config.aiming.horizontal_fov
vertical_fov           = config.aiming.vertical_fov
model_fps              = config.aiming.model_fps
bullet_velocity        = config.aiming.bullet_velocity
length_barrel          = config.aiming.length_barrel
camera_gap             = config.aiming.camera_gap
min_size_for_stdev     = config.aiming.min_size_for_stdev
std_error_bound        = config.aiming.std_error_bound
min_range              = config.aiming.min_range
max_range              = config.aiming.max_range
blue_light             = config.aiming.blue_light
blue_dark              = config.aiming.blue_dark
area_arrow_bound       = config.aiming.area_arrow_bound
center_image_offset    = config.aiming.center_image_offset
min_area               = config.aiming.min_area
r_timer                = config.aiming.r_timer
barrel_camera_gap      = config.aiming.barrel_camera_gap
sec_till_lock_lost     = config.aiming.sec_till_lock_lost
disable_bullet_drop    = config.aiming.disable_bullet_drop
disable_kalman_filters = config.aiming.disable_kalman_filters

# 
# init
# 
if not disable_kalman_filters: from subsystems.aiming.filter import KalmanFilter
x_circular_buffer = collections.deque(maxlen=config.aiming.min_size_for_stdev)
y_circular_buffer = collections.deque(maxlen=config.aiming.min_size_for_stdev)

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
    kalman_filter=None,
)

# 
# 
# main
# 
# 
def when_bounding_boxes_refresh():
    # import data
    found_robot       = runtime.modeling.found_robot
    best_bounding_box = runtime.modeling.best_bounding_box
    depth_image       = runtime.depth_image
    confidence        = runtime.modeling.current_confidence
    screen_center     = runtime.screen_center
    
    horizontal_angle, vertical_angle, should_shoot, horizonal_stdev, vertical_stdev, depth_amount, pixel_diff = (0, 0, 0, 0, 0, 0, 0)
    center_point, bullet_drop_point, kalman_point = (None, None, None)
    
    # 
    # update core aiming data
    # 
    if found_robot:
        prediction = best_bounding_box.center
        center_point = Position(prediction)
        depth_amount = get_distance_from_array(depth_image, best_bounding_box) # Find depth from camera to robot
        depth_out_of_bounds = depth_amount < min_range or depth_amount > max_range
    else:
        prediction = Position([0,0])
    
    # 
    # bullet drop
    # 
    if not disable_bullet_drop and found_robot:
        pixel_diff = bullet_drop_compensation_1(depth_amount)
        prediction[1] -= pixel_diff
    else:
        pixel_diff = 0
    bullet_drop_point = Position(prediction) # for exporting 
    
    # 
    # kalman filters
    # 
    if not disable_kalman_filters and found_robot:
        position_in_space = Position([
            prediction.x, # x,y value from original kalman code was NOT influcenced by bullet drop, but this one is
            prediction.y,
            depth_amount,
        ])
        # create if doesnt exist
        if runtime.aiming.kalman_filter is None:
            runtime.aiming.kalman_filter = KalmanFilter(model_fps)
            # TODO: calculate FPS on the fly
        
        # FIXME: where is the kalman filter updated? this is only prediciton
        kalman_prediction = runtime.aiming.kalman_filter.predict(
            data_for_imu=position_in_space, 
            realsense_frame=runtime.realsense.frame,
        )
        
        prediction = kalman_prediction[0:2]
    else:
        # reset whenever robot is lost (maybe make fake boxes for a few frames to prevent easily dropping a lock)
        runtime.aiming.kalman_filter = None
    kalman_point = Position(prediction) # for exporting 
    
    # 
    # compute offset (decide how much movement we need)
    # 
    if found_robot:
        horizontal_angle, vertical_angle = angle_from_center(prediction, screen_center)
        
    # 
    # update circular buffers
    # 
    if not found_robot or depth_out_of_bounds:
        x_circular_buffer.clear()
        y_circular_buffer.clear()
    else:
        x_circular_buffer.append(prediction[0])
        y_circular_buffer.append(prediction[1])
        horizonal_stdev = np.std(x_circular_buffer)
        vertical_stdev = np.std(y_circular_buffer)
        
    # 
    # should_shoot
    # 
    if not found_robot: # or depth_out_of_bounds
        should_shoot = False
    elif len(x_circular_buffer) >= min_size_for_stdev:
        prediction_error = average((horizonal_stdev, vertical_stdev))
        if prediction_error < std_error_bound:
            should_shoot = True
        else:
            should_shoot = False
    
    # 
    # should_look_around
    # 
    current_time = now()
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
    runtime.aiming.kalman_point       = kalman_point

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
    except:
        return 1

def bullet_drop_compensation_1(depth_amount):
    """
    Determines the bullet offset due to bullet drop and camera offset from shooter.
    Utilizes a function fitted from varying depth amounts.

    Input: Depth Amount of Bounding Box.
    Output: Offset in Pixels.
    """
    if depth_amount > 1 and depth_amount < 5:
        return (1.11208 * depth_amount ** 2) + (.1152 * depth_amount) + (-17.7672)
    else:
        return 0

def bullet_drop_core(radius, total_angle, proj_velocity, gimbal_pitch, time_interval):    
    """
    Determines the bullet offset due to bullet drop and camera offset from shooter.
    Fails due to not including all variables.

    Input: Depth Amount of Bounding Box.
    Output: Offset in Pixels.
    """
    geometric_height = radius * math.sin(total_angle)
    physical_height = proj_velocity * math.sin(gimbal_pitch) * time_interval + 0.5 * -9.8 * time_interval**2
    drop = geometric_height - physical_height   # drop is a POSITIVE VALUE
    return drop

def bullet_drop_compensation_2(depth_image, best_bounding_box, depth_amount, center, phi):
    """
    Determines the bullet offset due to bullet drop and camera offset from shooter.
    Utilizes theory and math.

    Input: Depth Amount of Bounding Box.
    Output: Offset in Pixels.
    """
    if phi is None:
        return 0

    diff_c =   stream_height/2  - (best_bounding_box[1] + 0.5* best_bounding_box[3])# pixels
    theta = math.atan((diff_c/stream_height/2) * math.tan(vertical_fov/2 * math.pi/180)) # theta in 
    diff_c = depth_amount * math.tan(theta) # convert diff_c to meters

    depth_from_pivot = length_barrel + depth_amount

    diff_p = float(diff_c) + float(camera_gap)
    rho = math.atan(diff_p/depth_from_pivot)
    psi = phi + rho
    range_p = depth_from_pivot/math.cos(rho)
    i = range_p * math.cos(psi)
    j = range_p * math.sin(psi)
    c = length_barrel * math.sin(psi)
    e = length_barrel * math.cos(psi)
    # t = 1.05*range_p/bullet_velocity
    t = (i - e)/(bullet_velocity * math.cos(psi))


    psi_f = math.asin((j-c-4.9*t**2) / (bullet_velocity*t) )
    # c = length_barrel * math.sin(psi_f)
    # e = length_barrel * math.cos(psi_f)
    # t_f = (i - e)/(bullet_velocity * math.cos(psi_f))
    # psi_f = math.asin((j-c-4.9*t_f**2) / (bullet_velocity*t_f) )

    j_check = (length_barrel * math.sin(psi_f)) + ((i - (length_barrel * math.cos(psi_f)))/(math.cos(psi_f))) * math.sin(psi_f) + 4.9 * ((i - (length_barrel * math.cos(psi_f)))/(bullet_velocity * math.cos(psi_f)))**2
    print("j: ", j, " j_check: ", j_check)
    change_psi = psi_f - psi
    change_p = stream_height/2/math.tan(vertical_fov/2*math.pi/180)*math.tan(change_psi)
    
    return change_p

def bullet_drop_compensation_3(depth_amount, gimbal_pitch, v_angle, proj_velocity = bullet_velocity):
    """
    Determines the bullet offset due to bullet drop and camera offset from shooter.
    Utilizes theory and math.

    Input: Depth Amount of Bounding Box.
    Output: Offset in Pixels.
    """
    radius = math.sqrt(depth_amount ** 2 + (depth_amount * math.tan(v_angle) + barrel_camera_gap) ** 2)
    total_angle = gimbal_pitch + math.atan2(depth_amount * math.tan(v_angle) + barrel_camera_gap, depth_amount)
    time_interval = (radius * math.cos(total_angle)) / (proj_velocity * math.cos(gimbal_pitch))
    geometric_height = radius * math.sin(total_angle)

    current_drop = bullet_drop_core(radius, total_angle, proj_velocity, gimbal_pitch, time_interval)

    new_height = geometric_height + current_drop
    horizontal_dist = radius * math.cos(total_angle)
    new_gimbal_pitch = math.atan2(new_height, horizontal_dist)

    new_radius = math.sqrt(new_height ** 2 + horizontal_dist ** 2)
    new_total_angle = math.atan2(horizontal_dist * math.tan(total_angle) + new_height, horizontal_dist)
    new_time_interval = (new_radius * math.cos(new_total_angle)) / (proj_velocity * math.cos(new_gimbal_pitch))

    future_drop = bullet_drop_core(new_radius, new_total_angle, proj_velocity, new_gimbal_pitch, new_time_interval)

    error = geometric_height - (new_height - future_drop)   # future drop is + and new_height is -
    final_height = new_height - error

    final_gimbal_pitch = math.atan2(final_height, horizontal_dist)
    return final_gimbal_pitch

def distance(point_1: tuple, point_2: tuple):
    """
    Returns the distance between two points.

    Input: Two points.
    Output: Distance in pixels.
    """

    distance = (sum((p1 - p2) ** 2.0 for p1, p2 in zip(point_1, point_2))) ** (1 / 2)
    return distance

def angle_from_center(prediction, screen_center):
    """
    Returns the x and y angles between the screen_center of the image and the screen_center of a bounding box.

    We send screen_center instead of importing 
    from info.yaml since recorded video footage could be different resolutions.

    Input: Bounding box and camera screen_center.
    Output: Horizontal and vertical angle in radians.
    """

    x_bbox_center, y_bbox_center, x_cam_center, y_cam_center = prediction[0], screen_center[1]*2-prediction[1], screen_center[0], screen_center[1]

    horizontal_angle = ((x_bbox_center-x_cam_center)/x_cam_center)*(horizontal_fov/2)
    vertical_angle = ((y_bbox_center-y_cam_center)/y_cam_center)*(vertical_fov/2)

    # print("horizontal_angle:",f"{horizontal_angle:.4f}"," vertical_angle:", f"{vertical_angle:.4f}", end=", ")

    return math.radians(horizontal_angle),math.radians(vertical_angle)

# bbox[x coordinate of the top left of the bounding box, y coordinate of the top left of the bounding box, width of box, height of box]
def world_coordinate(depth_frame, bbox):
    """
    Returns an estimate in position relative to the world.

    Input: Bounding Box and Depth Frame.
    Output: 3D point in space.
    """
    if not depth_frame:                     # if there is no aligned_depth_frame or color_frame then leave the loop
        return None
    # depth_intrin = depth_frame.profile.as_video_stream_profile().intrinsics
    depth_value = get_distance_from_array(depth_frame)
    # depth_pixel = [depth_intrin.ppx, depth_intrin.ppy]
    # depth_pixel = [bbox[0] + .5 * bbox[2], bbox[1] + .5 * bbox[3]]
    depth_point =   rs.deproject_pixel_to_point(bbox, depth_value)
    return depth_point

def pixel_coordinate(point):
    return rs.project_point_to_pixel(point)
