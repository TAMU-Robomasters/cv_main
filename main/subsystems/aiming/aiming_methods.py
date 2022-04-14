import numpy as np
import cv2
import math
import collections

from toolbox.globals import path_to, config, print
from toolbox.config import aiming

prediction_time     = aiming.prediction_time
stream_width        = aiming.stream_width
stream_height       = aiming.stream_height
stream_framerate    = aiming.stream_framerate
grid_size           = aiming.grid_size
horizontal_fov      = aiming.horizontal_fov
vertical_fov        = aiming.vertical_fov
model_fps           = aiming.model_fps
bullet_velocity     = aiming.bullet_velocity
length_barrel       = aiming.length_barrel
camera_gap          = aiming.camera_gap
std_buffer_size     = aiming.std_buffer_size
heat_buffer_size    = aiming.heat_buffer_size
rate_of_fire        = aiming.rate_of_fire
idle_counter        = aiming.idle_counter
std_error_bound     = aiming.std_error_bound
min_range           = aiming.min_range
max_range           = aiming.max_range
blue_light          = aiming.blue_light
blue_dark           = aiming.blue_dark
area_arrow_bound    = aiming.area_arrow_bound
center_image_offset = aiming.center_image_offset
min_area            = aiming.min_area
r_timer             = aiming.r_timer
barrel_camera_gap   = aiming.barrel_camera_gap

# these are used to ensure we are locked on a target
x_circular_buffer = collections.deque(maxlen=aiming.std_buffer_size)
y_circular_buffer = collections.deque(maxlen=aiming.std_buffer_size)

def visualize_depth_frame(depth_frame_array):
    """
    Displays a depth frame in a visualized color format.

    Input: Depth Frame.
    Output: None.
    """
    depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_frame_array, alpha = 0.04), cv2.COLORMAP_JET)# this puts a color efffect on the depth frame
    images = depth_colormap                              # use this for individual streams
    cv2.namedWindow('Align Example', cv2.WINDOW_NORMAL)   # names and shows the streams
    cv2.imwrite('depthmap.jpg', images)

    # # if you press escape or q you can cancel the process
    key = cv2.waitKey(1)
    print("press escape to cancel")
    if key & 0xFF == ord('q') or key == 27:
        cv2.destroyAllWindows()
    
def get_dist_from_array(depth_frame_array, bbox):
    """
    Determines the depth of a bounding box by choosing and filtering the depths of specific points in the bounding box.

    Input: Depth frame and bounding box.
    Output: Single depth value.
    """
    grid_size = aiming.grid_size

    try:
        x_top_left = bbox[0] 
        y_top_left = bbox[1]
        width = bbox[2]
        height = bbox[3]
        # this is used to add to the current_x and current_y so that we can get the different points in the 9x9 grid
        x_interval = width/grid_size
        y_interval = height/grid_size
        # stores the x and y of the last point in the grid we got the distance from
        curr_x = 0
        curr_y = 0
        distances = np.array([])
        # double for loop to go through 2D array of 9x9 grid
        for i in range(grid_size):
            curr_x += x_interval # add the interval you calculated to traverse through the 9x9 grid
            # print(curr_x)
            if (x_top_left+curr_x >= len(depth_frame_array[0])):
                break
            for j in range(grid_size):
                curr_y += y_interval # add the interval you calculated to traverse through the 9x9 grid
                # gets the distance of the point from the depth frame on the grid and appends to the array
                # print(curr_y)
                if (y_top_left+curr_y >= len(depth_frame_array)):
                    break
                distances = np.append(distances, depth_frame_array[int(y_top_left+curr_y)][int(x_top_left+curr_x)]/1000)
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
    depth_value = get_dist_from_array(depth_frame)
    # depth_pixel = [depth_intrin.ppx, depth_intrin.ppy]
    # depth_pixel = [bbox[0] + .5 * bbox[2], bbox[1] + .5 * bbox[3]]
    depth_point =   rs.deproject_pixel_to_point(bbox, depth_value)
    return depth_point

def pixel_coordinate(point):
    return rs.project_point_to_pixel(point)

def bullet_drop(radius, total_angle, proj_velocity, gimbal_pitch, time_interval):    
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

def bullet_drop_compensation(depth_image, best_bounding_box, depth_amount, center, phi):
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

def bullet_drop_compensation2(depth_amount, gimbal_pitch, v_angle, proj_velocity = bullet_velocity):
    """
    Determines the bullet offset due to bullet drop and camera offset from shooter.
    Utilizes theory and math.

    Input: Depth Amount of Bounding Box.
    Output: Offset in Pixels.
    """
    barrel_camera_gap = aiming.barrel_camera_gap
    radius = math.sqrt(depth_amount ** 2 + (depth_amount * math.tan(v_angle) + barrel_camera_gap) ** 2)
    total_angle = gimbal_pitch + math.atan2(depth_amount * math.tan(v_angle) + barrel_camera_gap, depth_amount)
    time_interval = (radius * math.cos(total_angle)) / (proj_velocity * math.cos(gimbal_pitch))
    geometric_height = radius * math.sin(total_angle)

    current_drop = bullet_drop(radius, total_angle, proj_velocity, gimbal_pitch, time_interval)

    new_height = geometric_height + current_drop
    horizontal_dist = radius * math.cos(total_angle)
    new_gimbal_pitch = math.atan2(new_height, horizontal_dist)

    new_radius = math.sqrt(new_height ** 2 + horizontal_dist ** 2)
    new_total_angle = math.atan2(horizontal_dist * math.tan(total_angle) + new_height, horizontal_dist)
    new_time_interval = (new_radius * math.cos(new_total_angle)) / (proj_velocity * math.cos(new_gimbal_pitch))

    future_drop = bullet_drop(new_radius, new_total_angle, proj_velocity, new_gimbal_pitch, new_time_interval)

    error = geometric_height - (new_height - future_drop)   # future drop is + and new_height is -
    final_height = new_height - error

    final_gimbal_pitch = math.atan2(final_height, horizontal_dist)
    return final_gimbal_pitch

def bullet_offset_compensation(depth_amount):
    """
    Determines the bullet offset due to bullet drop and camera offset from shooter.
    Utilizes a function fitted from varying depth amounts.

    Input: Depth Amount of Bounding Box.
    Output: Offset in Pixels.
    """
    if depth_amount > 1 and depth_amount < 5:
        return (1.11208 * depth_amount ** 2) + (.1152 * depth_amount) + (-17.7672)
    else:
        return None

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

    print("horizontal_angle:",f"{horizontal_angle:.4f}"," vertical_angle:", f"{vertical_angle:.4f}", end=", ")

    return math.radians(horizontal_angle),math.radians(vertical_angle)

def decide_shooting_location(best_bounding_box, screen_center, depth_image, x_circular_buffer, y_circular_buffer, using_tracker, kalman_filter=None):
    """
    Decide the shooting location based on the best bounding box. Find depth of detected robot. Update the circular buffers.

    Input: All detected bounding boxes with their confidences, center of the screen, depth image, and the circular buffers.
    Output: The predicted location to shoot, the depth, and how locked on we are.
    """

    # Location to shoot [x_obj_center, y_obj_center]
    depth_amount = get_dist_from_array(depth_image, best_bounding_box) # Find depth from camera to robot
    measured = [best_bounding_box[0]+best_bounding_box[2]/2, best_bounding_box[1]+best_bounding_box[3]/2, depth_amount]

    # Comment this if branch out in case kalman filters doesn't work
    # if kalman_filters and using_tracker:
    #     prediction[1] += getBulletDropPixels(depth_image,best_bounding_box)
    #     kalman_box = [prediction[0],prediction[1],z0] # Put data into format the kalman filter asks for
    #     prediction = kalman_filter.predict(kalman_box, frame) # figure out where to aim, returns (x_obj_center, y_obj_center)
    #     print("Kalman Filter updated Prediction to:",prediction)
    kalman_prediction = [0,0,0]
    if kalman_filter and using_tracker:
        kalman_prediction = kalman_filter.predict()
        kalman_filter.update(measured)

    depth_amount = get_dist_from_array(depth_image, best_bounding_box) # Find depth from camera to robot
    print(" best_bounding_box:",best_bounding_box, " prediction:", prediction, " depth_amount: ", depth_amount, end=", ")

    # phi = embedded_communication.get_phi()
    # print("PHI:",phi)
    # pixel_diff = 0
    # if phi:
    #     pixel_diff = 0 # Just here in case we comment out the next line
    #     pixel_diff = bullet_drop_compensation(depth_image,best_bounding_box,depth_amount,screen_center,phi)

    # pixel_diff = bullet_offset_compensation(depth_amount)
    # if pixel_diff is None:
    #     x_circular_buffer.clear()
    #     y_circular_buffer.clear()
    #     pixel_diff = 0

    # prediction[1] -= pixel_diff
    pixel_diff = kalman_prediction[1] - measured[1]
    x_std, y_std = update_circular_buffers(x_circular_buffer,y_circular_buffer,measured[0:2]) # Update buffers and measures of accuracy

    return kalman_prediction[0:2], depth_amount, x_std, y_std, pixel_diff

def initialize_tracker_and_kalman(best_bounding_box, track, color_image, kalman_filters):
    """
    Kalman filter logic with a bounding box.

    Input: Bounding boxes, confidences, screen center, track, and color image.
    Output: None.
    """
    
    kalman_filter = None
    best_bounding_box = track.init(color_image,tuple(best_bounding_box))
    print("Now Tracking a New Object.")

    # Reinitialize kalman filters
    if kalman_filters:
        kalman_filter = aiming.KalmanFilter(model_fps)
        print("Reinitialized Kalman Filter.")

    return best_bounding_box, kalman_filter

def update_circular_buffers(x_circular_buffer,y_circular_buffer,prediction):
    """
    Update circular buffers with latest prediction and recalculate accuracy through standard deviation.

    Input: Circular buffers for both components and the new prediction.
    Output: Standard deviations in both components.
    """

    x_circular_buffer.append(prediction[0])
    y_circular_buffer.append(prediction[1])
    x_std = np.std(x_circular_buffer)
    y_std = np.std(y_circular_buffer)

    return x_std, y_std

def send_shoot(xstd,ystd):
    """
    Decide whether to shoot or not.

    Input: Standard Deviations for both x and y.
    Output: Yes or no.
    """

    return 1 if ((xstd+ystd)/2 < std_error_bound) else 0
