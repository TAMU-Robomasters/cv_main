# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 19:43:04 2020

@author: xyf11
"""
import cv2
import os
from itertools import count
# relative imports
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print
from source.embedded_communication.embedded_main import embedded_communication
from source.videostream.videostream_main import get_latest_frame
import source.modeling.modeling_main as modeling
import source.tracking.tracking_main as tracker
import source.aiming.aiming_main as aiming

# import parameters from the info.yaml file
confidence = PARAMETERS["model"]["confidence"]
threshold = PARAMETERS["model"]["threshold"]
model_frequency = PARAMETERS["model"]["frequency"]

def setup(
        get_latest_frame=get_latest_frame,
        on_next_frame=None,
        modeling=modeling,
        tracker=tracker,
        aiming=aiming,
        #send_output=send_output
        embedded_communication=embedded_communication
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
            embedded_communication.send_output(x, y)
    
    # 
    # option #2
    # 
    def synchronous_with_tracker():
        """
        the 2nd main function
        - no multiprocessing
        - does use the tracker(KCF)
        """

    
        # model needs to run on first iteration
        best_bounding_box = None

        for counter in count(start=0, step=1): # counts up infinitely starting at 0

            # grabs frame and ends loop if we reach the last one
            frame = get_latest_frame()   
            if frame is None:
                break

            # run model every model_frequency frames or whenever the tracker fails
            if counter % model_frequency == 0 or (best_bounding_box is None):
                # call model and initialize tracker
                boxes, confidences, classIDs = modeling.get_bounding_boxes(frame, confidence, threshold)
                best_bounding_box = tracker.init(frame,boxes)
            else:
                best_bounding_box = tracker.update(frame)

            # optional value for debugging/testing
            if not (on_next_frame is None) :
                x, y = aiming.aim([best_bounding_box] if best_bounding_box else [])

                if best_bounding_box:
                    on_next_frame(counter, frame, ([best_bounding_box], [1]), (x,y))      
                    # send data to embedded
                    embedded_communication.send_output(x, y)
                else:
                    on_next_frame(counter, frame, ([], []), (x,y))
                
    
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