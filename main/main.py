# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 19:43:04 2020

@author: xyf11
"""
# library imports
import multiprocessing
import cv2
import os
import numpy as np
from itertools import count
from multiprocessing import Manager, Process,Value,Array
from multiprocessing.managers import BaseManager
import math
import time
import datetime
import collections

# relative imports
from toolbox.globals import MACHINE, PATHS, PARAMETERS, print
from subsystems.embedded_communication.embedded_main import embedded_communication
import subsystems.modeling._tests.test_modeling as test_modeling
import subsystems.tracking._tests.test_tracking as test_tracking
import subsystems.aiming.depth_camera as camera_methods

# import parameters from the info.yaml file
confidence      = PARAMETERS["model"]["confidence"]
threshold       = PARAMETERS["model"]["threshold"]
model_frequency = PARAMETERS["model"]["frequency"]

model_fps        = PARAMETERS['aiming']['model_fps']
grid_size        = PARAMETERS['aiming']['grid_size']
horizontal_fov   = PARAMETERS['aiming']['horizontal_fov']
vertical_fov     = PARAMETERS['aiming']['vertical_fov']
stream_width     = PARAMETERS['aiming']['stream_width']
stream_height    = PARAMETERS['aiming']['stream_height']
framerate        = PARAMETERS['aiming']['stream_framerate']
horizontal_fov   = PARAMETERS['aiming']['horizontal_fov']
vertical_fov     = PARAMETERS['aiming']['vertical_fov']
std_buffer_size  = PARAMETERS['aiming']['std_buffer_size']
heat_buffer_size = PARAMETERS['aiming']['heat_buffer_size']
rate_of_fire     = PARAMETERS['aiming']['rate_of_fire']
idle_counter     = PARAMETERS['aiming']['idle_counter']
std_error_bound  = PARAMETERS['aiming']['std_error_bound']
min_range        = PARAMETERS['aiming']['min_range']
max_range        = PARAMETERS['aiming']['max_range']

grab_frame      = PARAMETERS['videostream']['testing']['grab_frame']
record_interval = PARAMETERS['videostream']['testing']['record_interval']
with_gui        = PARAMETERS['testing']['open_each_frame']

color_video_location = PATHS['record_video_output_color']

def setup(
        team_color,
        get_frame = None,
        on_next_frame = None,
        modeling = test_modeling,
        tracker = test_tracking,
        aiming = None,
        embedded_communication = embedded_communication,
        live_camera = False,
        kalman_filters = False,
        with_gui = False,
        filter_team_color = False,
        video_output = None
    ):
    """
    This function is used to connect main with other modules.
    It can be connected to simulated/testing versions of other modules (laptop)
    or it can be connected to actual versions (tx2).
    
    Since we are testing multiple versions of main functions
    this returns a list of the all the different main functions.
    """

    
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
    
    def get_optimal_bounding_box(boxes,confidences,screen_center):
        """
        Decide the single best bounding box to aim at using a score system.

        Input: All detected bounding boxes with their confidences and the screen_center location of the image.
        Output: Best bounding box and its confidence.
        """

        best_bounding_box = boxes[0]
        best_score = 0
        cf = 0
        normalization_constant = distance((screen_center[0]*2,screen_center[1]*2),(screen_center[0],screen_center[1])) # Find constant used to scale distance part of score to 1

        # Sequentially iterate through all bounding boxes
        for i in range(len(boxes)):
            bbox = boxes[i]
            score = (1 - distance(screen_center,(bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2))/ normalization_constant) + confidences[i] # Compute score using distance and confidence

            # Make current box the best if its score is the best so far
            if score > best_score:
                best_bounding_box = boxes[i]
                best_score = score
                cf = confidences[i]
        
        return best_bounding_box, cf

    def send_shoot(xstd,ystd):
        """
        Decide whether to shoot or not.

        Input: Standard Deviations for both x and y.
        Output: Yes or no.
        """

        return 1 if ((xstd+ystd)/2 < std_error_bound) else 0

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


    def parse_frame(frame, frame_number):
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

    
    def decide_shooting_location(boxes, confidences, screen_center, depth_image, x_circular_buffer, y_circular_buffer):
        """
        Decide the shooting location based on the best bounding box. Find depth of detected robot. Update the circular buffers.

        Input: All detected bounding boxes with their confidences, center of the screen, depth image, and the circular buffers.
        Output: The predicted location to shoot, the depth, and how locked on we are.
        """

        best_bounding_box, cf = get_optimal_bounding_box(boxes, confidences, screen_center)

        # Location to shoot [x_obj_center, y_obj_center]
        prediction = [ best_bounding_box[0]+best_bounding_box[2]/2, best_bounding_box[1]+best_bounding_box[3]/2]
        depth_amount = camera_methods.get_dist_from_array(depth_image, best_bounding_box) # Find depth from camera to robot
        print(" best_bounding_box:",best_bounding_box, " prediction:", prediction, " depth_amount: ", depth_amount)

        # phi = embedded_communication.get_phi()
        # print("PHI:",phi)
        # pixel_diff = 0
        # if phi:
        #     pixel_diff = 0 # Just here in case we comment out the next line
        #     pixel_diff = camera_methods.bullet_drop_compensation(depth_image,best_bounding_box,depth_amount,screen_center,phi)

        pixel_diff = camera_methods.bullet_offset_compensation(depth_amount)
        if pixel_diff is None:
            x_circular_buffer.clear()
            y_circular_buffer.clear()
            pixel_diff = 0
        prediction[1] -= pixel_diff
        x_std, y_std = update_circular_buffers(x_circular_buffer,y_circular_buffer,prediction) # Update buffers and measures of accuracy

        return prediction, depth_amount, x_std, y_std,


    def send_embedded_command(found_robot, horizontal_angle, vertical_angle, depth_amount, x_circular_buffer, y_circular_buffer, x_std, y_std):
        """
        Tell embedded where to shoot and whether or not to shoot.

        Input: If a robot was detected, the angles to turn by, the depth, the circular buffers for x and y, and how locked on we are.
        Output: None.
        """

        if found_robot:
            # Send embedded the angles to turn to and the accuracy, make accuracy terrible if we dont have enough data in buffer 
            if depth_amount < min_range or depth_amount > max_range:
                x_circular_buffer.clear()
                y_circular_buffer.clear()
                shoot = embedded_communication.send_output(horizontal_angle, vertical_angle, 0)
            elif len(x_circular_buffer) == std_buffer_size:
                send_shoot_val = send_shoot(x_std,y_std)
                shoot = embedded_communication.send_output(horizontal_angle, vertical_angle,send_shoot_val)
            else:
                shoot = embedded_communication.send_output(horizontal_angle, vertical_angle, 0)
        else:
            # Clears buffers since no robots detected
            x_circular_buffer.clear()
            y_circular_buffer.clear()
            embedded_communication.send_output(0, 0, 0) # Tell embedded to stay still 
            print(" bounding_boxes: []")
    
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
        print(f'\rframe#: {frame_number} model took: {iteration_time:.4f}sec,', sep='', end='', flush=True)

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
    
    def kalman_logic(boxes, confidences, screen_center, track, color_image):
        """
        Kalman filter logic with a bounding box.

        Input: Bounding boxes, confidences, screen center, track, and color image.
        Output: None.
        """
        best_bounding_box = kalman_filter = None
        # Continue control logic if we detected atleast a single bounding box
        if len(boxes) != 0:
            # Get the best bounding box and initialize the tracker
            best_bounding_box, cf = get_optimal_bounding_box(boxes,confidences,screen_center)
            if best_bounding_box:
                best_bounding_box = track.init(color_image,tuple(best_bounding_box))
                print("Now Tracking a New Object.")

                # Reinitialize kalman filters
                if kalman_filters:
                    kalman_filter = aiming.Filter(model_fps)
                    print("Reinitialized Kalman Filter.")

        return best_bounding_box, kalman_filter
    
    #
    # option #1
    #
    def simple_synchronous():
        """
        This function is the most simple version of CV
        - no tracking
        - no multiprocessing/async/multithreading
        - no kalman filters since we need to track for that to be possible
        """

        frame_number = 0
        found_robot = False
        model = modeling.ModelingClass(team_color) # Create instance of modeling
        horizontal_angle = vertical_angle = x_std = y_std = depth_amount = pixel_diff = phi = cf = shoot = 0 # Initialize constants as "globals"
        x_circular_buffer, y_circular_buffer = collections.deque(maxlen=std_buffer_size), collections.deque(maxlen=std_buffer_size) # Used to ensure we are locked on a target

        while True:
            print.collect_prints = True
            initial_time = time.time()
            color_image, depth_image = parse_frame(get_frame(), frame_number)

            # Control logic for recorded video feed
            if not live_camera:
                if color_image is None:
                    break
                elif isinstance(color_image,int):
                    continue

            frame_number += 1
            boxes, confidences, class_ids, color_image = model.get_bounding_boxes(color_image, confidence, threshold, filter_team_color)
            screen_center = (color_image.shape[1] / 2, color_image.shape[0] / 2)

            # Continue control logic if we detected atleast a single bounding box
            if len(boxes)!=0:
                found_robot = True
                prediction, depth_amount, x_std, y_std = decide_shooting_location(boxes, confidences, screen_center, depth_image, x_circular_buffer, y_circular_buffer)
                horizontal_angle, vertical_angle = angle_from_center(prediction, screen_center)
            else: 
                found_robot = False

            send_embedded_command(found_robot, horizontal_angle, vertical_angle, depth_amount, x_circular_buffer, y_circular_buffer, x_std, y_std)
            display_information(found_robot, initial_time, frame_number, color_image, depth_image, horizontal_angle, vertical_angle, depth_amount, pixel_diff, x_std, y_std, cf, shoot, phi)

            # Save modeled video for recorded video feed
            if not (on_next_frame is None):
                on_next_frame(frame_number, color_image, (boxes, confidences), (horizontal_angle,vertical_angle))

    # 
    # option #2
    # 
    def synchronous_with_tracker():
        """
        the 2nd main function
        - no multiprocessing
        - does use the tracker(KCF)
        - uses kalman filters
        """

        # Initialize base variables as "globals" for the method
        counter = 1
        frame_number = 0
        cf = 0
        best_bounding_box = None
        reset_position_counter = 0
        horizontal_angle = vertical_angle = x_std = y_std = depth_amount = pixel_diff = phi = cf = shoot = 0 # Initialize constants as "globals"


        # Create two circular buffers to store predicted shooting locations (used to ensure we are locked on a target)
        x_circular_buffer, y_circular_buffer = collections.deque(maxlen=std_buffer_size), collections.deque(maxlen=std_buffer_size)
        
        # initialize model and tracker classes
        track = tracker.TrackingClass()
        model = modeling.ModelingClass(team_color)
        kalman_filter = None

        while True: # Counts up infinitely starting at 0
            initial_time = time.time()
            color_image, depth_image = parse_frame(get_frame(), frame_number)

            # Control logic for recorded video feed
            if not live_camera:
                if color_image is None:
                    break
                elif isinstance(color_image,int):
                    continue

            frame_number+=1
            counter+=1
            screen_center = (color_image.shape[1] / 2, color_image.shape[0] / 2) # Finds the coordinate for the screen_center of the screen
            
            # Run model every model_frequency frames or whenever the tracker fails
            if counter % model_frequency == 0 or (best_bounding_box is None):
                counter=1
                best_bounding_box = None
                boxes, confidences, class_ids, color_image = model.get_bounding_boxes(color_image, confidence, threshold, filter_team_color) # Call model
                best_bounding_box, kalman_filter = kalman_logic(boxes, confidences, screen_center, track, color_image)
            else:
                best_bounding_box = track.update(color_image) # Get new position of bounding box from tracker

            horizontal_angle = vertical_angle = x_std = y_std = depth_amount = pixel_diff = phi = 0 # Initialize constants as "globals"

            # Continue control logic if we detected atleast a single bounding box
            if best_bounding_box is not None:
                found_robot = True
                reset_position_counter = 0

                prediction = [best_bounding_box[0]+best_bounding_box[2]/2,best_bounding_box[1]+best_bounding_box[3]/2] # Location to shoot [x_obj_center, y_obj_center]
                print(" prediction: ",prediction)

                # Comment this if branch out in case kalman filters doesn'initial_time work
                # if kalman_filters:
                #     prediction[1] += camera_methods.getBulletDropPixels(depth_image,best_bounding_box)
                    # kalman_box = [prediction[0],prediction[1],z0] # Put data into format the kalman filter asks for
                    # prediction = kalman_filter.predict(kalman_box, frame) # figure out where to aim, returns (x_obj_center, y_obj_center)
                    # print("Kalman Filter updated Prediction to:",prediction)

                depth_amount = camera_methods.get_dist_from_array(depth_image,best_bounding_box) # Find depth from camera to robot

                pixel_diff = camera_methods.bullet_offset_compensation(depth_amount)
                if pixel_diff is None:
                    x_circular_buffer.clear()
                    y_circular_buffer.clear()
                    pixel_diff = 0

                prediction[1] -= pixel_diff

                x_std, y_std = update_circular_buffers(x_circular_buffer,y_circular_buffer,prediction) # Update buffers and measures of accuracy
                horizontal_angle, vertical_angle = angle_from_center(prediction, screen_center) # Determine angles to turn by in both x,y components
                print("Angles calculated are horizontal_angle:",horizontal_angle,"and vertical_angle:",vertical_angle)

                # If gui is enabled then draw bounding boxes around the selected robot
                if with_gui:
                    cv2.rectangle(color_image, (int(best_bounding_box[0]), int(best_bounding_box[1])), (int(best_bounding_box[0]) + int(best_bounding_box[2]), int(best_bounding_box[1]) + int(best_bounding_box[3])), (255,0,0), 2)
            else:
                found_robot = False

            send_embedded_command(found_robot, horizontal_angle, vertical_angle, depth_amount, x_circular_buffer, y_circular_buffer, x_std, y_std)
            # Display time taken for single iteration of loop
            display_information(found_robot, initial_time, frame_number, color_image, depth_image, horizontal_angle, vertical_angle, depth_amount, pixel_diff, x_std, y_std, cf, shoot, phi)

            # Optional value for debugging/testing for video footage only
            if not (on_next_frame is None):
                on_next_frame(frame_number, color_image, ([best_bounding_box], [1])if best_bounding_box else ([], []),(horizontal_angle,vertical_angle))

    # return a list of the different main options
    return simple_synchronous, synchronous_with_tracker 
    
def begin_video_recording():
    """
    Run live video recording using nvenc.

    Input: None
    Output: Video object to add frames too.
    """

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

if __name__ == '__main__':
    # Relative imports here since pyrealsense requires camera to be plugged in or code will crash
    import videostream._tests.get_live_video_frame as live_video
    import aiming.filter as test_aiming

    camera = live_video.LiveFeed()
    video_output = None

    try:
        # Setup video recording configuration if enabled
        if record_interval>0:
            video_output = begin_video_recording()

        team_color = PARAMETERS['embedded_communication']['team_color']

        # Must send classes so multiprocessing is possible
        simple_synchronous, synchronous_with_tracker,multiprocessing_with_tracker = setup(
            team_color,
            get_frame = camera.get_live_video_frame, 
            modeling = test_modeling,
            tracker = test_tracking,
            aiming = test_aiming,
            live_camera = True,
            kalman_filters = False,
            with_gui = False,
            filter_team_color = True,
            video_output = video_output
        )

        simple_synchronous() # CHANGE THIS LINE FOR DIFFERENT MAIN METHODS

    finally:
        # Save video output
        if video_output:
            print("Saving Recorded Video")
            video_output.release()
            print("Finished Saving Video")