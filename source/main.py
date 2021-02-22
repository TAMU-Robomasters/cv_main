# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 19:43:04 2020

@author: xyf11
"""
import multiprocessing
import cv2
import os
import numpy as np
from itertools import count
from multiprocessing import Manager, Process,Value,Array
from multiprocessing.managers import BaseManager

# relative imports
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print
from source.embedded_communication.embedded_main import embedded_communication
import source.modeling._tests.test_modeling as test_modeling
import source.tracking._tests.test_tracking as test_tracking
import source.aiming._tests.test_aiming as test_aiming
from source.videostream._tests.get_next_video_frame import get_next_video_frame

# import parameters from the info.yaml file
confidence = PARAMETERS["model"]["confidence"]
threshold = PARAMETERS["model"]["threshold"]
model_frequency = PARAMETERS["model"]["frequency"]
grabFrame = PARAMETERS['videostream']['testing']['grab_frame']

def setup(
        get_frame = None,
        on_next_frame=None,
        modeling=test_modeling,
        tracker=test_tracking,
        aiming=test_aiming,
        embedded_communication=embedded_communication,
        testing = True
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
        model = modeling.modelingClass() # create instance of modeling

        while True:
            frame = get_frame()  
            color_frame = None
            color_image = None           
            depth_frame = None
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

            frameNumber+=1
            # run the model
            boxes, confidences, classIDs, color_image = model.get_bounding_boxes(color_image, confidence, threshold)
            
            # figure out where to aim
            x, y = aiming.aim(boxes)

            # optional value for debugging/testing
            if not (on_next_frame is None):
                on_next_frame(frameNumber, color_image, (boxes, confidences), (x,y))
            
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
            color_frame = None
            color_image = None           
            depth_frame = None
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

            frameNumber+=1
            counter+=1
            # run model every model_frequency frames or whenever the tracker fails
            if counter % model_frequency == 0 or (best_bounding_box is None):
                counter=1
                # call model and initialize tracker
                boxes, confidences, classIDs, color_image = model.get_bounding_boxes(color_image, confidence, threshold)
                best_bounding_box = track.init(frame,boxes)
            else:
                best_bounding_box = track.update(color_image)

            # optional value for debugging/testing
            x, y = aiming.aim([best_bounding_box] if best_bounding_box else [])

            if not (on_next_frame is None) :
                on_next_frame(frameNumber, color_image, ([best_bounding_box], [1])if best_bounding_box else ([], []), (x,y))
                
    

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
            color_frame = None
            color_image = None           
            depth_frame = None
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

            if collectFrames.value:
                betweenFrames.append(color_image)
            realCounter+=1
            frameNumber+=1
            # run model if there is no current bounding box in another process
            if best_bounding_box[:] == [-1,-1,-1,-1]:
                if process is None or process.is_alive()==False:
                    collectFrames.value = True
                    process = Process(target=modelMulti,args=(color_image,confidence,threshold,best_bounding_box,track,model,betweenFrames,collectFrames))
                    process.start() 
                    realCounter=1

            else:
            # run model in another process every model_frequency frames
                if realCounter % model_frequency == 0:
                    # call model and initialize tracker
                    if process is None or process.is_alive()==False:
                        collectFrames.value = True
                        process = Process(target=modelMulti,args=(color_image,confidence,threshold,best_bounding_box,track,model,betweenFrames,collectFrames))
                        process.start() 
                
                #track bounding box, even if we are modeling for a new one
                if track.trackerAlive():
                    try:
                        potentialbbox = track.update(color_image)
                        best_bounding_box[:] = potentialbbox if potentialbbox else [-1,-1,-1,-1]
                    except:
                        best_bounding_box[:] = [-1,-1,-1,-1]
                else:
                    best_bounding_box[:] = [-1,-1,-1,-1]

            # figure out where to aim
            x, y = aiming.aim(best_bounding_box[:])
            
            # optional value for debugging/testing
            if not (on_next_frame is None) :
                on_next_frame(frameNumber, color_image, ([best_bounding_box[:]], [1])if best_bounding_box[:] != [-1,-1,-1,-1] else ([], []), (x,y))
            
            # send data to embedded
            embedded_communication.send_output(x, y)
        process.join() # make sure process is complete to avoid errors being thrown

    
    # return a list of the different main options
    return simple_synchronous, synchronous_with_tracker,multiprocessing_with_tracker
    

if __name__ == '__main__':
    # setup mains with real inputs/outputs
    import source.videostream._tests.get_live_video_frame as liveVideo
    camera = liveVideo.liveFeed()
    simple_synchronous, synchronous_with_tracker,multiprocessing_with_tracker = setup(
        get_frame = camera.get_live_video_frame, 
        modeling=test_modeling,
        tracker=test_tracking,
        aiming=test_aiming,
        testing = False
    )
    # TODO: CREATE INSTANCE OF AIMING CLASS WHERE IT INITIALIZES PIPELINE, THIS WILL BE THE BEGINNING OF AIMING INTEGRATION

    simple_synchronous()