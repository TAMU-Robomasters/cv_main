# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 19:43:04 2020

@author: xyf11
"""
import multiprocessing
import cv2
import os
from itertools import count
from multiprocessing import Manager, Process,Value,Array
from multiprocessing.managers import BaseManager
# relative imports
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print
from source.embedded_communication.embedded_main import embedded_communication
import source.modeling.modeling_main as modeling
import source.tracking.tracking_main as tracker
import source.aiming.aiming_main as aiming

# import parameters from the info.yaml file
confidence = PARAMETERS["model"]["confidence"]
threshold = PARAMETERS["model"]["threshold"]
model_frequency = PARAMETERS["model"]["frequency"]
def setup(
        get_frame = None,
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
        frameNumber = 0 # used for on_next_frame
        # create instance of modeling
        model = modeling.modelingClass()

        while True:
            # get the latest image from the camera
            frame = get_frame()
            # stop loop if using get_next_video_frame 
            if frame is None:
                break
            # stop loop if using get_latest_video_frame(required since there are 3 cases for get_latest_video_frame compared to the 2 cases in get_next_video_frame)
            if isinstance(frame,int):
                continue

            frameNumber+=1
            # run the model
            boxes, confidences, classIDs, frame = model.get_bounding_boxes(frame, confidence, threshold)
            
            # figure out where to aim
            x, y = aiming.aim(boxes)
            
            # optional value for debugging/testing
            if not (on_next_frame is None):
                on_next_frame(frameNumber, frame, (boxes, confidences), (x,y))
            
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

        counter = 1
        frameNumber = 0 # used for on_next_frame
        # model needs to run on first iteration
        best_bounding_box = None
        
        # create shared instances of tracker and model between multiprocesses
        track = tracker.trackingClass()
        model = modeling.modelingClass()

        while True: # counts up infinitely starting at 0
            # grabs frame and ends loop if we reach the last one
            frame = get_frame()
            # stop loop if using get_next_video_frame   
            if frame is None:
                break
            # stop loop if using get_latest_video_frame(required since there are 3 cases for get_latest_video_frame compared to the 2 cases in get_next_video_frame)
            if isinstance(frame,int):
                continue

            frameNumber+=1
            counter+=1
            # run model every model_frequency frames or whenever the tracker fails
            if counter % model_frequency == 0 or (best_bounding_box is None):
                counter=1
                # call model and initialize tracker
                boxes, confidences, classIDs, frame = model.get_bounding_boxes(frame, confidence, threshold)
                best_bounding_box = track.init(frame,boxes)
            else:
                best_bounding_box = track.update(frame)

            # optional value for debugging/testing
            x, y = aiming.aim([best_bounding_box] if best_bounding_box else [])

            if not (on_next_frame is None) :
                on_next_frame(frameNumber, frame, ([best_bounding_box], [1])if best_bounding_box else ([], []), (x,y))
                
    

    def modelMulti(frame,confidence,threshold,best_bounding_box,track,model,betweenFrames,collectFrames):
        #run the model and update best bounding box to the new bounding box if it exists, otherwise keep tracking the old bounding box
        boxes, confidences, classIDs, frame = model.get_bounding_boxes(frame, confidence, threshold)
        potentialbbox = track.init(frame,boxes)

        for f in range(len(betweenFrames)):
            if potentialbbox is None:
                break
            potentialbbox = track.update(betweenFrames[f])
            print(potentialbbox)

        best_bounding_box[:] = potentialbbox if potentialbbox else [-1,-1,-1,-1]
        betweenFrames[:] = []
        collectFrames.value = False
        
    def multiprocessing_with_tracker():
        """
        the 3nd main function
        - multiprocessing
        - does use the tracker(KCF)
        """
        # Manager is required in order to share instances of classes between processes
        class MyManager(BaseManager):
            pass
        MyManager.register('tracker', tracker.trackingClass)
        MyManager.register('modeling', modeling.modelingClass)
        manager = MyManager()
        manager.start()

        realCounter = 1
        frameNumber = 0 # used for on_next_frame
        best_bounding_box = Array('d',[-1,-1,-1,-1]) # must be of Array type to be modified by multiprocess
        process = None
        variableManager = multiprocessing.Manager()
        betweenFrames = variableManager.list()
        collectFrames = Value('b',False)


        # create shared instances of tracker and model between multiprocesses
        track = manager.tracker()
        model = manager.modeling()

        while True:
            # grabs frame and ends loop if we reach the last one
            frame = get_frame()
            # stop loop if using get_next_video_frame   
            if frame is None:
                break
            # stop loop if using get_latest_video_frame(required since there are 3 cases for get_latest_video_frame compared to the 2 cases in get_next_video_frame)
            if isinstance(frame,int):
                continue
            if collectFrames.value:
                betweenFrames.append(frame)
            realCounter+=1
            frameNumber+=1
            # run model if there is no current bounding box in another process
            if best_bounding_box[:] == [-1,-1,-1,-1]:
                if process is None or process.is_alive()==False:
                    collectFrames.value = True
                    process = Process(target=modelMulti,args=(frame,confidence,threshold,best_bounding_box,track,model,betweenFrames,collectFrames))
                    process.start() 
                    realCounter=1

            else:
            # run model in another process every model_frequency frames
                if realCounter % model_frequency == 0:
                    # call model and initialize tracker
                    if process is None or process.is_alive()==False:
                        collectFrames.value = True
                        process = Process(target=modelMulti,args=(frame,confidence,threshold,best_bounding_box,track,model,betweenFrames,collectFrames))
                        process.start() 
                
                #track bounding box, even if we are modeling for a new one
                if track.trackerAlive():
                    try:
                        potentialbbox = track.update(frame)
                        best_bounding_box[:] = potentialbbox if potentialbbox else [-1,-1,-1,-1]
                    except:
                        best_bounding_box[:] = [-1,-1,-1,-1]
                else:
                    best_bounding_box[:] = [-1,-1,-1,-1]

            # figure out where to aim
            x, y = aiming.aim(best_bounding_box[:])
            
            # optional value for debugging/testing
            if not (on_next_frame is None) :
                on_next_frame(frameNumber, frame, ([best_bounding_box[:]], [1])if best_bounding_box[:] != [-1,-1,-1,-1] else ([], []), (x,y))
            
            # send data to embedded
            embedded_communication.send_output(x, y)
        process.join() # make sure process is complete to avoid errors being thrown

    
    # return a list of the different main options
    return simple_synchronous, synchronous_with_tracker,multiprocessing_with_tracker
    
if __name__ == '__main__':
    # setup mains with real inputs/outputs
    simple_synchronous, synchronous_with_tracker,multiprocessing_with_tracker = setup()
    
    # for now, default to simple_synchronous
    simple_synchronous