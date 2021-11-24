import numpy as np
import time

from toolbox.globals import MACHINE, PATHS, PARAMETERS, print
from subsystems.integration.import_parameters import *


def update_live_recorded_video(color_image, frame_number):
    """
    Update the recorded video (live camera) by adding the latest frame.

    Input: Frame number.
    Output: None.
    """

    # Add frame to video recording based on recording frequency
    if video_output and frame_number % record_interval == 0:
        print(" saving_frame:",frame_number)
        video_output.write(color_image)

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

def parse_frame(frame, frame_number, live_camera):
    """
    Convert the frame into a color image and depth image.

    Input: Frame and frame number.
    Output: Color image and depth image.
    """
    color_image = None
    depth_image = None

    if live_camera:
        # Parse color and depth images into usable formats
        color_frame = frame.get_color_frame()
        color_image = np.asanyarray(color_frame.get_data()) 
        depth_frame = frame.get_depth_frame() 
        depth_image = np.asanyarray(depth_frame.get_data()) 

        update_live_recorded_video(color_image, frame_number)
    else:
        if frame is None: # If there is no more frames then end method
            # flush the print
            print(" "*100)
            print.collect_prints = False
            print("")
            color_image = None
        if isinstance(frame,int): # If an int was returned we simply had a faulty frame
            color_image = 0
        color_image = frame

    return color_image, depth_image

def display_information(found_robot, initial_time, frame_number, color_image, depth_image, horizontal_angle, vertical_angle, depth_amount, pixel_diff, x_std, y_std, cf, shoot, phi):  
    """
    Display text on the screen and draw bounding box on robot.

    Input: Information to be displayed
    Output: None.
    """

    # If gui is enabled then draw bounding boxes around the selected robot
    if with_gui and found_robot:
        cv2.rectangle(found_robot, color_image, (best_bounding_box[0], best_bounding_box[1]), (best_bounding_box[0] + best_bounding_box[2], best_bounding_box[1] + best_bounding_box[3]), (255,0,0), 2)  

    # Display time taken for single iteration of loop
    iteration_time = time.time()-initial_time
    # relase all print info on one line
    print(" "*200)
    print.collect_prints = False
    # print(f'\rframe#: {frame_number} model took: {iteration_time:.4f}sec,', sep='', end='', flush=True)
    print(f'\r', sep='', end='', flush=True)

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

def begin_video_recording():
    """
    Run live video recording using nvenc.

    Input: None
    Output: Video object to add frames too.
    """

    color_video_location = PATHS['record_video_output_color']
    
    # Setup video output path based on date and counter
    c = 1
    file_path = color_video_location.replace(".do_not_sync",datetime.datetime.now().strftime("%Y-%m-%d")+"_"+str(c)+".do_not_sync")
    while os.path.isfile(file_path):
        c += 1
        file_path = color_video_location.replace(".do_not_sync",datetime.datetime.now().strftime("%Y-%m-%d")+"_"+str(c)+".do_not_sync")

    # Start up video output
    gst_out = "appsrc ! video/x-raw, format=BGR ! queue ! videoconvert ! video/x-raw,format=BGRx ! nvvidconv ! nvv4l2h264enc ! h264parse ! matroskamux ! filesink location="+file_path
    video_output = cv2.VideoWriter(gst_out, cv2.CAP_GSTREAMER, 0, float(framerate), (int(stream_width), int(stream_height)))
    if not video_output.isOpened():
        print("Failed to open output")

    return video_output