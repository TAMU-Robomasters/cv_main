import numpy as np
import cv2
import math
from toolbox.globals import PARAMETERS,print

bullet_velocity = PARAMETERS['aiming']['bullet_velocity']
length_barrel = PARAMETERS['aiming']['length_barrel']
camera_gap = PARAMETERS['aiming']['camera_gap']
vertical_fov = PARAMETERS['aiming']['vertical_fov']
stream_height = PARAMETERS['aiming']['stream_height']
barrel_camera_gap = PARAMETERS['aiming']['barrel_camera_gap']

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