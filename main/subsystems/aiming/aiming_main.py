from subsystems.aiming.aiming_methods import *

x_std, y_std, depth_amount, pixel_diff = (0, 0, 0, 0)
def aim(best_bounding_box, cf, boxes, screen_center, depth_image):
    global x_std, y_std, depth_amount, pixel_diff
    horizontal_angle, vertical_angle, should_shoot = (0, 0, 0)
    # If we detected robots, find bounding box closest to center of screen and determine angles to turn by
    if len(boxes) > 0:
        # found_robot
        prediction, depth_amount, x_std, y_std, pixel_diff = decide_shooting_location(best_bounding_box, screen_center, depth_image, x_circular_buffer, y_circular_buffer, False)
        horizontal_angle, vertical_angle = angle_from_center(prediction, screen_center)
        # Send embedded the angles to turn to and the accuracy, make accuracy terrible if we dont have enough data in buffer 
        if depth_amount < min_range or depth_amount > max_range:
            x_circular_buffer.clear()
            y_circular_buffer.clear()
            should_shoot = 0
        elif len(x_circular_buffer) == std_buffer_size:
            send_shoot_val = send_shoot(x_std, y_std)
    # no robots
    else: 
        x_circular_buffer.clear()
        y_circular_buffer.clear()
        print(" bounding_boxes: []")
        
    return horizontal_angle, vertical_angle, should_shoot, (x_std, y_std, depth_amount, pixel_diff)
