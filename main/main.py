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
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print
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

        # Calculates the distance using Python spagettie
        distance = (sum((p1 - p2) ** 2.0 for p1, p2 in zip(point_1, point_2))) ** (1 / 2)
        # Returns the distance between two points
        return distance
    
    def angle_from_center(x_bbox_center, y_bbox_center, x_cam_center, y_cam_center):
        """
        Returns the x and y angles between the center of the image and the center of a bounding box.

        We send x_cam_center and y_cam_center instead of importing 
        from info.yaml since recorded video footage could be different resolutions.

        Input: Bounding box and camera center components.
        Output: Horizontal and vertical angle in radians.
        """
        horizontal_angle = ((x_bbox_center-x_cam_center)/x_cam_center)*(horizontal_fov/2)
        vertical_angle = ((y_bbox_center-y_cam_center)/y_cam_center)*(vertical_fov/2)

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
    
    def get_optimal_bounding_box(boxes,confidences,center):
        """
        Decide the single best bounding box to aim at using a score system.

        Input: All detected bounding boxes with their confidences and the center location of the image.
        Output: Best bounding box and its confidence.
        """

        best_bounding_box = boxes[0]
        best_score = 0
        cf = 0
        normalization_constant = distance((center[0]*2,center[1]*2),(center[0],center[1])) # Find constant used to scale distance part of score to 1

        # Sequentially iterate through all bounding boxes
        for i in range(len(boxes)):
            bbox = boxes[i]
            score = (1 - distance(center,(bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2))/ normalization_constant) + confidences[i] # Compute score using distance and confidence

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

        frame_number = 0 # Used for on_next_frame
        model = modeling.ModelingClass(team_color) # Create instance of modeling
        horizontal_angle = vertical_angle = x_std = y_std = depth_amount = pixel_diff = phi = cf = shoot = 0 # Initialize constants as "globals"
        reset_position_counter = 0 # Send embedded whether to reset to default position

        # Create two circular buffers to store predicted shooting locations (used to ensure we are locked on a target)
        x_circular_buffer = collections.deque(maxlen=std_buffer_size)
        y_circular_buffer = collections.deque(maxlen=std_buffer_size)

        # Create two circular buffers to store frame times and whether we shoot or not to calculate barrel heat.
        ft_circular_buffer = collections.deque(maxlen=heat_buffer_size)
        shoot_circular_buffer = collections.deque(maxlen=heat_buffer_size)

        while True:
            heat_estimate = max(10*(rate_of_fire/(1/np.mean(ft_circular_buffer)))* (np.sum(shoot_circular_buffer)-50*np.sum(ft_circular_buffer)),0) # Equation to calculate barrel heat
            print("Heat Estimate:",heat_estimate)

            t = time.time()
            frame = get_frame()  
            color_image = None           
            depth_image = None

            # Differentiate between live camera feed and recorded video data
            if live_camera:
                # Parse color and depth images into usable formats
                color_frame = frame.get_color_frame()
                color_image = np.asanyarray(color_frame.get_data()) 
                depth_frame = frame.get_depth_frame() 
                depth_image = np.asanyarray(depth_frame.get_data()) 

                # Add frame to video recording based on recording frequency
                if video_output and frame_number % record_interval == 0:
                    print("Saving Frame",frame_number)
                    video_output.write(color_image)
            else:
                if frame is None: # If there is no more frames then end method
                    break
                if isinstance(frame,int): # If an int was returned we simply had a faulty frame
                    continue
                color_image = frame

            frame_number+=1

            boxes, confidences, class_ids, color_image = model.get_bounding_boxes(color_image, confidence, threshold, filter_team_color) # Run the model
            center = (color_image.shape[1] / 2, color_image.shape[0] / 2) # Finds the coordinate for the center of the screen

            # Continue control logic if we detected atleast a single bounding box
            if len(boxes)!=0:
                reset_position_counter = 0
                best_bounding_box, cf = get_optimal_bounding_box(boxes, confidences, center)
                # Location to shoot [x_obj_center, y_obj_center]
                prediction = [ best_bounding_box[0]+best_bounding_box[2]/2, best_bounding_box[1]+best_bounding_box[3]/2]
                depth_amount = camera_methods.get_dist_from_array(depth_image, best_bounding_box) # Find depth from camera to robot

                print("Best Bounding Box",best_bounding_box)
                print("Prediction is:",prediction)
                print("DEPTH:",depth_amount)

                # phi = embedded_communication.get_phi()
                # print("PHI:",phi)
                # pixel_diff = 0
                # if phi:
                #     pixel_diff = 0 # Just here in case we comment out the next line
                #     pixel_diff = camera_methods.bullet_drop_compensation(depth_image,best_bounding_box,depth_amount,center,phi)

                pixel_diff = camera_methods.bullet_offset_compensation(depth_amount)
                if pixel_diff is None:
                    x_circular_buffer.clear()
                    y_circular_buffer.clear()
                    pixel_diff = 0
                prediction[1] -= pixel_diff

                x_std, y_std = update_circular_buffers(x_circular_buffer,y_circular_buffer,prediction) # Update buffers and measures of accuracy
                horizontal_angle, vertical_angle = angle_from_center(prediction[0],center[1]*2-prediction[1],center[0],center[1]) # Determine angles to turn by in both x,y components

                print("Angles calculated are horizontal_angle:",horizontal_angle,"and vertical_angle:",vertical_angle)

                # Send embedded the angles to turn to and the accuracy, make accuracy terrible if we dont have enough data in buffer 
                if depth_amount < min_range or depth_amount > max_range:
                    x_circular_buffer.clear()
                    y_circular_buffer.clear()
                    shoot = embedded_communication.send_output(horizontal_angle, vertical_angle, 0)
                    shoot_circular_buffer.append(0)
                elif len(x_circular_buffer) == std_buffer_size:
                    send_shoot_val = send_shoot(x_std,y_std)
                    shoot = embedded_communication.send_output(horizontal_angle, vertical_angle,send_shoot_val)
                    shoot_circular_buffer.append(send_shoot_val)
                else:
                    shoot = embedded_communication.send_output(horizontal_angle, vertical_angle, 0)
                    shoot_circular_buffer.append(0)
                
                # If gui is enabled then draw bounding boxes around the selected robot
                if with_gui:
                    cv2.rectangle(color_image, (best_bounding_box[0], best_bounding_box[1]), (best_bounding_box[0] + best_bounding_box[2], best_bounding_box[1] + best_bounding_box[3]), (255,0,0), 2)
            else:
                # Clears buffers since no robots detected
                x_circular_buffer.clear()
                y_circular_buffer.clear()
                shoot_circular_buffer.append(0)
                reset_position_counter+=1
                embedded_communication.send_output(0, 0, 0) # Tell embedded to stay still 
                print("No Bounding Boxes Found")

            # Display time taken for single iteration of loop
            iteration_time = time.time()-t
            ft_circular_buffer.append(iteration_time)
            print('Processing frame',frame_number,'took',iteration_time,"seconds for model only\n")

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

            # Optional value for debugging/testing for video footage only
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
        # Create two circular buffers to store predicted shooting locations (used to ensure we are locked on a target)
        x_circular_buffer = collections.deque(maxlen=std_buffer_size)
        y_circular_buffer = collections.deque(maxlen=std_buffer_size)
        
        # initialize model and tracker classes
        track = tracker.TrackingClass()
        model = modeling.ModelingClass(team_color)
        kalman_filter = None

        while True: # Counts up infinitely starting at 0
            print()
            t = time.time()
            frame = get_frame()  
            color_image = None    
            depth_image = None

            # Differentiate between live camera feed and recorded video data
            if live_camera:
                # Parse color and depth images into usable formats
                color_frame = frame.get_color_frame()
                color_image = np.asanyarray(color_frame.get_data()) 
                depth_frame = frame.get_depth_frame() 
                depth_image = np.asanyarray(depth_frame.get_data()) 

                # Add frame to video recording based on recording frequency
                if video_output and frame_number % record_interval == 0:
                    print("Saving Frame",frame_number)
                    video_output.write(color_image)
            else:
                if frame is None: # If there is no more frames then end method
                    break
                if isinstance(frame,int): # If an int was returned we simply had a faulty frame
                    continue
                color_image = frame


            frame_number+=1
            counter+=1

            center = (color_image.shape[1] / 2, color_image.shape[0] / 2) # Finds the coordinate for the center of the screen
            
            # Run model every model_frequency frames or whenever the tracker fails
            if counter % model_frequency == 0 or (best_bounding_box is None):
                counter=1
                best_bounding_box = None
                boxes, confidences, class_ids, color_image = model.get_bounding_boxes(color_image, confidence, threshold, filter_team_color) # Call model

                # Continue control logic if we detected atleast a single bounding box
                if len(boxes) != 0:
                    # Get the best bounding box and initialize the tracker
                    best_bounding_box, cf = get_optimal_bounding_box(boxes,confidences,center)
                    if best_bounding_box:
                        best_bounding_box = track.init(color_image,tuple(best_bounding_box))
                        print("Now Tracking a New Object.")

                        # Reinitialize kalman filters
                        if kalman_filters:
                            kalman_filter = aiming.Filter(model_fps)
                            print("Reinitialized Kalman Filter.")
            else:
                best_bounding_box = track.update(color_image) # Get new position of bounding box from tracker

            horizontal_angle = vertical_angle = x_std = y_std = depth_amount = pixel_diff = phi = 0 # Initialize constants as "globals"

            # Continue control logic if we detected atleast a single bounding box
            if best_bounding_box is not None:
                reset_position_counter = 0
                prediction = [best_bounding_box[0]+best_bounding_box[2]/2,best_bounding_box[1]+best_bounding_box[3]/2] # Location to shoot [x_obj_center, y_obj_center]
                print("Prediction is:",prediction)

                # Comment this if branch out in case kalman filters doesn't work
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
                horizontal_angle, vertical_angle = angle_from_center(prediction[0],prediction[1],center[0],center[1]) # Determine angles to turn by in both x,y components
                print("Angles calculated are horizontal_angle:",horizontal_angle,"and vertical_angle:",vertical_angle)

                # Send embedded the angles to turn to and the accuracy, make accuracy terrible if we dont have enough data in buffer                
                if depth_amount < min_range or depth_amount > max_range:
                    x_circular_buffer.clear()
                    y_circular_buffer.clear()
                    embedded_communication.send_output(horizontal_angle, vertical_angle, 0) # Tell embedded to stay still 
                elif len(x_circular_buffer) == std_buffer_size:
                    send_shoot_val = send_shoot(x_std,y_std)
                    embedded_communication.send_output(horizontal_angle, vertical_angle, send_shoot_val)
                else:
                    embedded_communication.send_output(horizontal_angle, vertical_angle, 0)

                # If gui is enabled then draw bounding boxes around the selected robot
                if with_gui:
                    cv2.rectangle(color_image, (int(best_bounding_box[0]), int(best_bounding_box[1])), (int(best_bounding_box[0]) + int(best_bounding_box[2]), int(best_bounding_box[1]) + int(best_bounding_box[3])), (255,0,0), 2)
            else:
                # Clears buffers since no robots detected
                x_circular_buffer.clear()
                y_circular_buffer.clear()
                reset_position_counter += 1
                embedded_communication.send_output(0, 0, 0,extra=(1 if reset_position_counter>=idle_counter else 0)) # Tell embedded to stay still and not shoot
                print("No Bounding Boxes Found")

            # Display time taken for single iteration of loop
            iteration_time = time.time() - t
            print('Processing frame',frame_number,'took',iteration_time,"seconds for model+tracker")

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
                
                if phi:
                    cv2.putText(color_image,"phi: "+str(np.round(phi,2)), (30,450) , font, font_scale, font_color, line_type)

                cv2.imshow("feed",color_image)
                cv2.waitKey(10)

            # Optional value for debugging/testing for video footage only
            if not (on_next_frame is None):
                on_next_frame(frame_number, color_image, ([best_bounding_box], [1])if best_bounding_box else ([], []),(horizontal_angle,vertical_angle))
                
    
    def model_multi(color_image, confidence, threshold, best_bounding_box, track, model, between_frames, collect_frames, center):
        # Run the model and update best bounding box to the new bounding box if it exists, otherwise keep tracking the old bounding box
        boxes, confidences, class_ids, color_image = model.get_bounding_boxes(color_image, confidence, threshold)
        bbox = None

        if len(boxes) != 0:
            # Makes a dictionary of bounding boxes using the bounding box as the key and its distance from the center as the value
            bboxes = {tuple(bbox): distance(center, (bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2)) for bbox in boxes}
            # Finds the centermost bounding box
            bbox = min(bboxes, key=bboxes.get)

        if bbox:
            potential_bounding_box = track.init(color_image,bbox)
            print(potential_bounding_box)

            for f in range(len(between_frames)):
                if potential_bounding_box is None:
                    break
                potential_bounding_box = track.update(between_frames[f])
                print(potential_bounding_box)

            best_bounding_box[:] = potential_bounding_box if potential_bounding_box else [-1,-1,-1,-1]
            between_frames[:] = []
            collect_frames.value = False
        
    def multiprocessing_with_tracker():
        """
        the 3nd main function
        - multiprocessing
        - does use the tracker(KCF)
        """
        # Manager is required in order to share instances of classes between processes
        class MyManager(BaseManager):
            pass
        MyManager.register('tracker', tracker.TrackingClass)
        MyManager.register('modeling', modeling.ModelingClass)
        manager = MyManager()
        manager.start()

        real_counter = 1
        frame_number = 0 # used for on_next_frame
        best_bounding_box = Array('d',[-1,-1,-1,-1]) # must be of Array type to be modified by multiprocess
        process = None
        variable_manager = multiprocessing.Manager()
        between_frames = variable_manager.list()
        collect_frames = Value('b',False)


        # create shared instances of tracker and model between multiprocesses
        track = manager.tracker()
        model = manager.modeling()

        while True:
            # grabs frame and ends loop if we reach the last one
            frame = get_frame()  
            color_image = None           
            depth_image = None

            if testing == False:
                color_frame = frame.get_color_frame()
                color_image = np.asanyarray(color_frame.get_data()) 
                depth_frame = frame.get_depth_frame() 
                depth_image = np.asanyarray(depth_frame.get_data()) 
            else:
                if frame is None:
                    break
                if isinstance(frame,int):
                    continue
                color_image = frame

            if collect_frames.value:
                between_frames.append(color_image)
            real_counter+=1
            frame_number+=1

            # Finds the coordinate for the center of the screen
            center = (color_image.shape[1] / 2, color_image.shape[0] / 2) # (x from columns/2, y from rows/2)
            
            # run model if there is no current bounding box in another process
            if best_bounding_box[:] == [-1,-1,-1,-1]:
                if process is None or process.is_alive()==False:
                    collect_frames.value = True
                    process = Process(target=model_multi, args=(color_image, confidence, threshold, best_bounding_box, track, model, between_frames, collect_frames, center))
                    process.start() 
                    real_counter=1

            else:
            # run model in another process every model_frequency frames
                if real_counter % model_frequency == 0:
                    # call model and initialize tracker
                    if process is None or process.is_alive()==False:
                        collect_frames.value = True
                        process = Process(target=model_multi,args=(color_image, confidence, threshold, best_bounding_box, track, model, between_frames, collect_frames, center))
                        process.start() 
                
                #track bounding box, even if we are modeling for a new one
                if track.tracker_alive():
                    try:
                        potential_bounding_box = track.update(color_image)
                        best_bounding_box[:] = potential_bounding_box if potential_bounding_box else [-1,-1,-1,-1]
                    except:
                        best_bounding_box[:] = [-1,-1,-1,-1]
                else:
                    best_bounding_box[:] = [-1,-1,-1,-1]

            # figure out where to aim
            if testing == False:
                z0 = camera_methods.get_dist_from_array(depth_image,best_bounding_box,grid_size)
                kalman_box = [best_bounding_box[0],best_bounding_box[1],z0] # Put data into format the kalman filter asks for
                prediction = kalman_filter.predict(kalman_box) # figure out where to aim
            
                # send data to embedded
                horizontal_angle, vertical_angle = angle_from_center(prediction[0],prediction[1],center[0],center[1],horizontal_fov,vertical_fov) # (x_obj,y_obj,x_cam/2,y_cam/2,h_fov,v_fov)
                embedded_communication.send_output(horizontal_angle, vertical_angle)

            # optional value for debugging/testing
            if not (on_next_frame is None) :
                on_next_frame(frame_number, color_image, ([best_bounding_box[:]], [1])if best_bounding_box[:] != [-1,-1,-1,-1] else ([], []), (0,0))
            
        process.join() # make sure process is complete to avoid errors being thrown

    # return a list of the different main options
    return simple_synchronous, synchronous_with_tracker,multiprocessing_with_tracker
    
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

        # GPIO Based Team Color Decision Making
        # led_pin = 12
        # but_pin = 18
        # GPIO.setmode(GPIO.BOARD)  # BOARD pin-numbering scheme
        # GPIO.setup(led_pin, GPIO.OUT)  # LED pin set as output
        # GPIO.setup(but_pin, GPIO.IN)  # Button pin set as input

        # # Initial state for LEDs:
        # GPIO.output(led_pin, GPIO.LOW)
        # team_color = GPIO.input(but_pin)
        # print("GPIO:",team_color)
        # team_color = 1 if team_color == 0 else 0

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
        # GPIO.cleanup()