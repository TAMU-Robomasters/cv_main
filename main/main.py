# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 19:43:04 2020

@author: xyf11
"""
# library imports
import cv2
import os
import numpy as np
from itertools import count
import math
import time
import datetime
import collections

# relative imports
from toolbox.globals import PATHS, config, print
from subsystems.embedded_communication.embedded_main import embedded_communication
import subsystems.modeling.modeling_main as modeling
import subsystems.tracking.tracking_main as tracking
import subsystems.aiming.aiming_main as aiming
import subsystems.aiming.aiming_methods as aiming_methods
import subsystems.integration.integration_methods as integration_methods

def setup(
        on_next_frame=None,
        video_stream=None,
        modeling=modeling,
        tracker=tracking,
        aiming=aiming,
        embedded_communication=embedded_communication,
        live_camera=False,
        kalman_filters=False,
        with_gui=False,
        filter_team_color=False,
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
        - no kalman filters since we need to track for that to be possible
        """

        # Initialize default values
        model = modeling.ModelingClass() # Create instance of modeling

        # Run detection infinitely
        for frame_number, (color_image, depth_image) in enumerate(video_stream.frames()):
            # Grab frame and record initial time
            print.collect_prints = True
            initial_time = time.time()
            
            # modeling
            boxes, confidences, class_ids, color_image = model.get_bounding_boxes(color_image, config.model.threshold, filter_team_color)
            screen_center = (color_image.shape[1] / 2, color_image.shape[0] / 2)
            best_bounding_box, cf = model.get_optimal_bounding_box(boxes, confidences, screen_center, aiming_methods.distance)
            # aiming
            horizontal_angle, vertical_angle, should_shoot, (x_std, y_std, depth_amount, pixel_diff) = aiming.aim(best_bounding_box, cf, boxes, screen_center, depth_image)
            # communication
            embedded_communication.send_output(horizontal_angle, vertical_angle, should_shoot)
            # logging
            found_robot = best_bounding_box is not None
            integration_methods.display_information(found_robot, initial_time, frame_number, color_image, depth_image, horizontal_angle, vertical_angle, depth_amount, pixel_diff, x_std, y_std, cf, should_shoot, 0)
            # testing/debugging
            if not (on_next_frame is None): on_next_frame(frame_number, color_image, (boxes, confidences), (horizontal_angle,vertical_angle))

    # 
    # option #2
    # 
    def synchronous_with_tracker():
        """
        the 2nd main function
        - does use the tracker (KCF)
        - does use kalman filters
        """

        # Initialize default values
        counter = 1
        best_bounding_box = kalman_filter = None
        horizontal_angle = vertical_angle = x_std = y_std = depth_amount = pixel_diff = phi = cf = shoot = 0
        x_circular_buffer, y_circular_buffer = collections.deque(maxlen=config.aiming.std_buffer_size), collections.deque(maxlen=config.aiming.std_buffer_size) # Used to ensure we are locked on a target
        track = tracker.TrackingClass()
        model = modeling.ModelingClass()

        a = 0
        start_time = time.time()

        # Run detection infinitely
        for frame_number, (color_image, depth_image) in enumerate(video_stream.frames()):
            # Grab frame and record initial time
            initial_time = time.time()

            counter+=1
            screen_center = (color_image.shape[1] / 2, color_image.shape[0] / 2) # Finds the coordinate for the screen_center of the screen
            
            # Run model, find best bbox, and re-initialize tracker/kalman filters every model.frequency frames or whenever the tracker fails
            if counter % config.model.frequency == 0 or (best_bounding_box is None):
                counter=1
                best_bounding_box = None
                boxes, confidences, class_ids, color_image = model.get_bounding_boxes(color_image, config.model.threshold, filter_team_color) # Call model
                if len(boxes)!=0:
                    best_bounding_box, cf = model.get_optimal_bounding_box(boxes, confidences, screen_center, aiming_methods.distance)
                    best_bounding_box, kalman_filter = aiming_methods.initialize_tracker_and_kalman(best_bounding_box, track, color_image, kalman_filters)
            else:
                best_bounding_box = track.update(color_image) # Get new position of bounding box from tracker

            # If we detected robots, determine angle to turn by
            if best_bounding_box is not None:
                # Find bounding box closest to center of screen and determine angles to turn by
                found_robot = True
                prediction, depth_amount, x_std, y_std = aiming_methods.decide_shooting_location(best_bounding_box, screen_center, depth_image, x_circular_buffer, y_circular_buffer, True, integration_methods.update_circular_buffers)
                horizontal_angle, vertical_angle = aiming_methods.angle_from_center(prediction, screen_center)
            else:
                found_robot = False

            # Actually move the robot to aim
            embedded_communication.send_embedded_command(found_robot, horizontal_angle, vertical_angle, depth_amount, x_circular_buffer, y_circular_buffer, x_std, y_std)
            integration_methods.display_information(found_robot, initial_time, frame_number, color_image, depth_image, horizontal_angle, vertical_angle, depth_amount, pixel_diff, x_std, y_std, cf, shoot, phi)

            # Save modeled frame for recorded video feed
            if not (on_next_frame is None):
                on_next_frame(frame_number, color_image, ([best_bounding_box], [1])if best_bounding_box else ([], []),(horizontal_angle,vertical_angle))

        fps = a / (time.time() - start_time)
        print("Average fps:", fps)

        # return a list of the different main options
        return simple_synchronous, synchronous_with_tracker 
    

if __name__ == '__main__':
    # Relative imports here since pyrealsense requires camera to be plugged in or code will crash
    # print("CAMERA",config.hardware.camera)
    # if config.hardware.camera == 'zed':
    #     from subsystems.videostream.zed import VideoStream
    # else:
    from subsystems.videostream.realsense import VideoStream
    
    video_stream = VideoStream()
    simple_synchronous, synchronous_with_tracker = setup(
        video_stream=video_stream,
        modeling=modeling,
        tracker=tracking,
        live_camera=True,
        kalman_filters=False,
        with_gui=False,
        filter_team_color=True,
    )
    try:
        simple_synchronous() # CHANGE THIS LINE FOR DIFFERENT MAIN METHODS
    finally:
        video_stream.save_video_if_needed()