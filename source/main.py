# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 19:43:04 2020

@author: xyf11
"""
import cv2
import os
from itertools import count
# relative imports
from toolbox.globals import PATHS, PARAMETERS
from source.embedded_communication.send_to_embedded import send_output
from source.videostream.videostream_main import get_latest_frame
import source.modeling.modeling_main as modeling
import source.tracking.tracking_main as tracker
import source.aiming.aiming_main as aiming

# import parameters from the info.yaml file
confidence = PARAMETERS["model"]["confidence"]
threshold = PARAMETERS["model"]["threshold"]

def setup(
        get_latest_frame=get_latest_frame,
        on_next_frame=None,
        modeling=modeling,
        tracker=tracker,
        aiming=aiming,
        send_output=send_output
    ):
    """
    this function is used to connect main with other modules
    it can be connected to simulated/testing versions of other modules (laptop)
    or it can be connected to actual versions (tx2)
    
    since we are testing multiple versions of main functions
    this returns a list of the all the different main functions
    """
    
    # 
    # option #1
    #
    def simple_synchronous():
        """
        this function is the most simple version of CV
        - no tracking
        - no multiprocessing/async/multithreading
        """
        
        for counter in count(start=0, step=1): # counts up infinitely starting at 0
            # get the latest image from the camera
            frame = get_latest_frame()
            if frame is None:
                print("assuming the video stream ended because latest frame is None")
                return
            
            # run the model
            boxes, confidences, classIDs = modeling.get_bounding_boxes(frame, confidence, threshold)
            
            # figure out where to aim
            x, y = aiming.aim(boxes)
            
            # optional value for debugging/testing
            if not (on_next_frame is None):
                on_next_frame(counter, frame, (boxes, confidences), (x,y))
            
            # send data to embedded
            send_output(x, y)
    
    # 
    # option #2
    # 
    def synchronous_with_tracker():
        """
        the 2nd main function
        - no multiprocessing
        - does use the tracker
        """
    
        # model needs to run on first iteration
        best_bounding_box = None

        for counter in count(start=0, step=1): # counts up infinitely starting at 0
            # runs for the first 450 frames of video since there is a faulty frame later on
            if counter == 450:
                break
            frame = get_latest_frame()

            # run model every 40 frames or whenever the tracker fails
            if counter % 40 == 0 or (best_bounding_box is None):
                # call model and initialize tracker
                if frame is not None:
                    boxes, confidences, classIDs = modeling.get_bounding_boxes(frame, confidence, threshold)
                    best_bounding_box = tracker.init(frame,boxes)
                else:
                    # set tracking to have failed on faulty frames
                    best_bounding_box=None
            else:
                best_bounding_box = tracker.update(frame)


            # figure out where to aim
            if best_bounding_box:
                x, y = aiming.aim(best_bounding_box)
                
                # optional value for debugging/testing
                if not (on_next_frame is None) :
                    on_next_frame(counter, frame, ([best_bounding_box], [1]), (x,y))
                
                # send data to embedded
                send_output(x, y)
    
    # 
    # option #3
    # 
    # multiprocessing: have main/tracker/videostream/aiming as seperate processes
    # have modeling only be called once tracker fails
    
    # 
    # option #4
    # 
    # have multiple processes and have them all running all the time
    # tracker pulls the latest model rather than waiting to fail before calling modeling
    
    # return a list of the different main options
    return simple_synchronous, synchronous_with_tracker
    
if __name__ == '__main__':
    # setup mains with real inputs/outputs
    simple_synchronous, synchronous_with_tracker = setup()
    
    # for now, default to simple_synchronous
    synchronous_with_tracker