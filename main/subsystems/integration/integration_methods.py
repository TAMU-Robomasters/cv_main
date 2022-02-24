import numpy as np
import time

from toolbox.globals import PATHS, config, print

def display_information(found_robot, initial_time, frame_number, color_image, depth_image, horizontal_angle, vertical_angle, depth_amount, pixel_diff, x_std, y_std, cf, shoot, phi):  
    """
    Display text on the screen and draw bounding box on robot.

    Input: Information to be displayed
    Output: None.
    """
    with_gui = config.testing.open_each_frame

    # If gui is enabled then draw bounding boxes around the selected robot
    if with_gui and found_robot:
        cv2.rectangle(found_robot, color_image, (best_bounding_box[0], best_bounding_box[1]), (best_bounding_box[0] + best_bounding_box[2], best_bounding_box[1] + best_bounding_box[3]), (255,0,0), 2)  

    # Display time taken for single iteration of loop
    iteration_time = time.time()-initial_time
    # relase all print info on one line
    print(" "*200)
    print(f'\nframe#: {frame_number} model took: {iteration_time:.4f}sec,', sep='', end='', flush=True)

    # Show live feed is gui is enabled
    if with_gui:
        from toolbox.image_tools import add_text
        add_text(text="horizontal_angle: "+str(np.round(horizontal_angle,2)), location=(30, 50), image=color_image)
        add_text(text="vertical_angle: "  +str(np.round(vertical_angle,2))  , location=(30,100), image=color_image)
        add_text(text="depth_amount: "    +str(np.round(depth_amount,2))    , location=(30,150), image=color_image)
        add_text(text="pixel_diff: "      +str(np.round(pixel_diff,2))      , location=(30,200), image=color_image)
        add_text(text="x_std: "           +str(np.round(x_std,2))           , location=(30,250), image=color_image)
        add_text(text="y_std: "           +str(np.round(y_std,2))           , location=(30,300), image=color_image)
        add_text(text="confidence: "      +str(np.round(cf,2))              , location=(30,350), image=color_image)
        add_text(text="fps: "             +str(np.round(1/iteration_time,2)), location=(30,400), image=color_image)
        add_text(text="shoot: "           +str(shoot)                       , location=(30,450), image=color_image)

        if phi:
            cv2.putText(color_image,"Phi: "+str(np.round(phi,2)), (30,450) , font, font_scale, font_color, line_type)

        cv2.imshow("RGB Feed",color_image)
        cv2.waitKey(10)
