import numpy as np
import cv2
import math

from toolbox.globals import PARAMETERS,print
from subsystems.integration.import_parameters import *
import subsystems.aiming.filter as aiming
import pyrealsense2.pyrealsense2 as realsense

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
    grid_size = PARAMETERS['aiming']['grid_size']

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
def world_coordinate_rs(depth_frame, bbox, profile):
    """
    Returns an estimate in position relative to the world.

    Input: Bounding Box and Depth Frame.
    Output: 3D point in space.
    """
    if not depth_frame:                     # if there is no aligned_depth_frame or color_frame then leave the loop
        return None
    
    depth_intrin = depth_frame.profile.as_video_stream_profile().intrinsics
    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()
    depth_point = realsense.rs2_deproject_pixel_to_point(depth_intrin, bbox, get_dist_from_array(depth_frame, bbox))
    # depth_point = deproject_pixel_to_point(bbox, get_dist_from_array(depth_frame))
    return depth_point

def world_coordinate_zed(depth_frame, bbox, profile):
    """
    Returns an estimate in position relative to the world.

    Input: Bounding Box and Depth Frame.
    Output: 3D point in space.
    """
    if not depth_frame:                     # if there is no aligned_depth_frame or color_frame then leave the loop
        return None
    
    depth_intrin = depth_frame.profile.as_video_stream_profile().intrinsics
    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()
    depth_point = realsense.rs2_deproject_pixel_to_point(depth_intrin, bbox, get_dist_from_array(depth_frame, bbox))
    # depth_point = deproject_pixel_to_point(bbox, get_dist_from_array(depth_frame))
    return depth_point

def pixel_coordinate(depth_frame, point):
    depth_intrin = depth_frame.profile.as_video_stream_profile().intrinsics
    return realsense.rs2_project_point_to_pixel(depth_intrin, point)

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
    barrel_camera_gap = PARAMETERS["aiming"]["barrel_camera_gap"]
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

    print("horizontal_angle:",f"{horizontal_angle:.4f}"," vertical_angle:", f"{vertical_angle:.4f}")

    return math.radians(horizontal_angle),math.radians(vertical_angle)

def decide_shooting_location(profile, kalman_filter, frame, best_bounding_box, screen_center, depth_image, x_circular_buffer, y_circular_buffer, kalman_filters, using_tracker, update_circular_buffers):
    """
    Decide the shooting location based on the best bounding box. Find depth of detected robot. Update the circular buffers.

    Input: All detected bounding boxes with their confidences, center of the screen, depth image, and the circular buffers.
    Output: The predicted location to shoot, the depth, and how locked on we are.
    """

    # Location to shoot [x_obj_center, y_obj_center]
    prediction = [best_bounding_box[0]+best_bounding_box[2]/2, best_bounding_box[1]+best_bounding_box[3]/2]

    # Comment this if branch out in case kalman filters doesn't work
    if kalman_filters and kalman_filter and using_tracker:
        # prediction[1] += getBulletDropPixels(depth_image,best_bounding_box)
        z0 = get_dist_from_array(depth_image,best_bounding_box)
        kalman_box = [prediction[0],prediction[1],z0] # Put data into format the kalman filter asks for
        print("PREDICTION OLD", kalman_box)

        prediction = kalman_filter.predict(kalman_box, frame, world_coordinate, pixel_coordinate, profile) # figure out where to aim, returns (x_obj_center, y_obj_center)
        print("Kalman Filter updated Prediction to:",prediction)

    depth_amount = get_dist_from_array(depth_image, best_bounding_box) # Find depth from camera to robot
    print(" best_bounding_box:",best_bounding_box, " prediction:", prediction, " depth_amount: ", depth_amount)

    # phi = embedded_communication.get_phi()
    # print("PHI:",phi)
    # pixel_diff = 0
    # if phi:
    #     pixel_diff = 0 # Just here in case we comment out the next line
    #     pixel_diff = bullet_drop_compensation(depth_image,best_bounding_box,depth_amount,screen_center,phi)

    pixel_diff = bullet_offset_compensation(depth_amount)
    if pixel_diff is None:
        x_circular_buffer.clear()
        y_circular_buffer.clear()
        pixel_diff = 0

    prediction[1] -= pixel_diff
    x_std, y_std = update_circular_buffers(x_circular_buffer,y_circular_buffer,prediction) # Update buffers and measures of accuracy

    return prediction, depth_amount, x_std, y_std

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
        kalman_filter = aiming.Filter(model_fps)
        print("Reinitialized Kalman Filter.")

    return best_bounding_box, kalman_filter