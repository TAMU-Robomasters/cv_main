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
import subsystems.aiming.aiming_methods as aiming_methods
import subsystems.integration.integration_methods as integration_methods
from subsystems.integration.import_parameters import *

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
    or it can be connected to actual versions (tx2/xavier).
    
    Since we are testing multiple versions of main functions
    this returns a list of the all the different main functions.
    """
    
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

        found_robot = False
        model = modeling.ModelingClass(team_color) # Create instance of modeling
        frame_number = horizontal_angle = vertical_angle = x_std = y_std = depth_amount = pixel_diff = phi = cf = shoot = 0 # Initialize constants as "globals"
        x_circular_buffer, y_circular_buffer = collections.deque(maxlen=std_buffer_size), collections.deque(maxlen=std_buffer_size) # Used to ensure we are locked on a target

        while True:
            print.collect_prints = True
            initial_time = time.time()
            color_image, depth_image = integration_methods.parse_frame(get_frame(), frame_number, live_camera)

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
                best_bounding_box, cf = model.get_optimal_bounding_box(boxes, confidences, screen_center)
                prediction, depth_amount, x_std, y_std = aiming_methods.decide_shooting_location(best_bounding_box, screen_center, depth_image, x_circular_buffer, y_circular_buffer, False)
                horizontal_angle, vertical_angle = aiming_methods.angle_from_center(prediction, screen_center)
            else: 
                found_robot = False

            embedded_communication.send_embedded_command(found_robot, horizontal_angle, vertical_angle, depth_amount, x_circular_buffer, y_circular_buffer, x_std, y_std)
            integration_methods.display_information(found_robot, initial_time, frame_number, color_image, depth_image, horizontal_angle, vertical_angle, depth_amount, pixel_diff, x_std, y_std, cf, shoot, phi)

            # Save modeled frame for recorded video feed
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
        best_bounding_box = kalman_filter = None
        frame_number = horizontal_angle = vertical_angle = x_std = y_std = depth_amount = pixel_diff = phi = cf = shoot = 0 # Initialize constants as "globals"
        x_circular_buffer, y_circular_buffer = collections.deque(maxlen=std_buffer_size), collections.deque(maxlen=std_buffer_size) # Used to ensure we are locked on a target
        
        # Initialize model and tracker classes
        track = tracker.TrackingClass()
        model = modeling.ModelingClass(team_color)

        while True: # Counts up infinitely starting at 0
            initial_time = time.time()
            color_image, depth_image = integration_methods.parse_frame(get_frame(), frame_number, live_camera)

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
                if len(boxes)!=0:
                    best_bounding_box, cf = model.get_optimal_bounding_box(boxes, confidences, screen_center)
                    best_bounding_box, kalman_filter = aiming_methods.initialize_tracker_and_kalman(best_bounding_box, track, color_image, kalman_filters)
            else:
                best_bounding_box = track.update(color_image) # Get new position of bounding box from tracker

            # Continue control logic if we detected atleast a single bounding box
            if best_bounding_box is not None:
                found_robot = True
                prediction, depth_amount, x_std, y_std = aiming_methods.decide_shooting_location(best_bounding_box, screen_center, depth_image, x_circular_buffer, y_circular_buffer, True)
                horizontal_angle, vertical_angle = aiming_methods.angle_from_center(prediction, screen_center)
            else:
                found_robot = False

            embedded_communication.send_embedded_command(found_robot, horizontal_angle, vertical_angle, depth_amount, x_circular_buffer, y_circular_buffer, x_std, y_std)
            integration_methods.display_information(found_robot, initial_time, frame_number, color_image, depth_image, horizontal_angle, vertical_angle, depth_amount, pixel_diff, x_std, y_std, cf, shoot, phi)

            # Save modeled frame for recorded video feed
            if not (on_next_frame is None):
                on_next_frame(frame_number, color_image, ([best_bounding_box], [1])if best_bounding_box else ([], []),(horizontal_angle,vertical_angle))

    # return a list of the different main options
    return simple_synchronous, synchronous_with_tracker 
    

if __name__ == '__main__':
    # Relative imports here since pyrealsense requires camera to be plugged in or code will crash
    import videostream._tests.get_live_video_frame as live_video
    import aiming.filter as test_aiming

    camera = live_video.LiveFeed()
    video_output = None

    try:
        # Setup video recording configuration if enabled
        if record_interval>0:
            video_output = integration_methods.begin_video_recording()

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