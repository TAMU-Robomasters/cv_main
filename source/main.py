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
import source.aiming.filter as test_aiming
import source.aiming.depth_camera as cameraMethods

# import parameters from the info.yaml file
confidence = PARAMETERS["model"]["confidence"]
threshold = PARAMETERS["model"]["threshold"]
model_frequency = PARAMETERS["model"]["frequency"]
grabFrame = PARAMETERS['videostream']['testing']['grab_frame']
predictionTime = PARAMETERS['aiming']['prediction_time']
gridSize = PARAMETERS['aiming']['grid_size']
horizontalFOV = PARAMETERS['aiming']['horizontal_fov']
verticalFOV = PARAMETERS['aiming']['vertical_fov']

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

    def distance(point_1: tuple, point_2: tuple):
        # Calculates the distance using Python spagettie
        distance = (sum((p1 - p2) ** 2.0 for p1, p2 in zip(point_1, point_2))) ** (1 / 2)
        # Returns the distance between two points
        return distance
    
    def angleFromCenter(xObject,yObject,xCamCenter,yCamCenter,hFOV,vFOV):
        hAngle = ((xObject-xCamCenter)/xCamCenter)*(hFOV/2)
        vAngle = ((yObject-yCamCenter)/yCamCenter)*(vFOV/2)
        return hAngle,vAngle
    
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
        kalmanFilter = None

        while True:
            frame = get_frame()  
            color_image = None           
            depth_image = None

            if testing == False:
                kalmanFilter = aiming.Filter(predictionTime)
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
            
            # Finds the coordinate for the center of the screen
            center = (color_image.shape[1] / 2, color_image.shape[0] / 2) # (x/2 from columns/2,y/2 from rows/2)
            print(center)
            if len(boxes)!=0:
                # Makes a dictionary of bounding boxes using the bounding box as the key and its distance from the center as the value
                bboxes = {tuple(bbox): distance(center, (bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2)) for bbox in boxes}
                # Finds the centermost bounding box
                best_bounding_box = min(bboxes, key=bboxes.get)

                prediction = [best_bounding_box[0],best_bounding_box[1],0] # row, column, depth

                if testing == False:
                    z0 = cameraMethods.getDistFromArray(depth_image,best_bounding_box,gridSize)
                    kalmanBox = [best_bounding_box[0],best_bounding_box[1],z0] # Put data into format the kalman filter asks for
                    prediction = kalmanFilter.predict(kalmanBox) # figure out where to aim, returns (row,column,depth,vRow,vCol,vDepth)
                
                # send data to embedded
                hAngle, vAngle = angleFromCenter(prediction[1],center[1]-prediction[0],center[0],center[1],horizontalFOV,verticalFOV) # (xObj,yObj,xCam/2,yCam/2,hFov,vFov)
                print("ANGLES: ",hAngle,vAngle)
                embedded_communication.send_output(hAngle, vAngle)
                
            # optional value for debugging/testing
            if not (on_next_frame is None):
                on_next_frame(frameNumber, color_image, (boxes, confidences), (0,0))
    
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
        kalmanFilter = None

        while True: # counts up infinitely starting at 0
            # grabs frame and ends loop if we reach the last one
            frame = get_frame()  
            color_image = None           
            depth_image = None

            if testing == False:
                kalmanFilter = aiming.Filter(predictionTime)
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

            # Finds the coordinate for the center of the screen
            center = (color_image.shape[1] / 2, color_image.shape[0] / 2)

            # run model every model_frequency frames or whenever the tracker fails
            if counter % model_frequency == 0 or (best_bounding_box is None):
                counter=1
                # call model
                boxes, confidences, classIDs, color_image = model.get_bounding_boxes(color_image, confidence, threshold)

                if len(boxes) != 0:
                    # Makes a dictionary of bounding boxes using the bounding box as the key and its distance from the center as the value
                    bboxes = {tuple(bbox): distance(center, (bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2)) for bbox in boxes}
                    # Finds the centermost bounding box
                    best_bounding_box = min(bboxes, key=bboxes.get)

                    best_bounding_box = track.init(color_image,best_bounding_box)
            else:
                best_bounding_box = track.update(color_image)


            if best_bounding_box is not None:
                prediction = [best_bounding_box[0],best_bounding_box[1],0]

                if testing == False:
                    z0 = cameraMethods.getDistFromArray(depth_image,best_bounding_box,gridSize)
                    kalmanBox = [best_bounding_box[0],best_bounding_box[1],z0] # Put data into format the kalman filter asks for
                    prediction = kalmanFilter.predict(kalmanBox) # figure out where to aim
                
                # send data to embedded
                hAngle, vAngle = angleFromCenter(prediction[1],prediction[0],center[0],center[1],horizontalFOV,verticalFOV) # send column,row since using array but calculating angle for image
                embedded_communication.send_output(hAngle, vAngle)
                
            # optional value for debugging/testing
            if not (on_next_frame is None):
                on_next_frame(frameNumber, color_image, ([best_bounding_box], [1])if best_bounding_box else ([], []), (0,0))
                
    

    def modelMulti(color_image,confidence,threshold,best_bounding_box,track,model,betweenFrames,collectFrames,center):
        #run the model and update best bounding box to the new bounding box if it exists, otherwise keep tracking the old bounding box
        boxes, confidences, classIDs, color_image = model.get_bounding_boxes(color_image, confidence, threshold)
        bbox = None

        if len(boxes) != 0:
            # Makes a dictionary of bounding boxes using the bounding box as the key and its distance from the center as the value
            bboxes = {tuple(bbox): distance(center, (bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2)) for bbox in boxes}
            # Finds the centermost bounding box
            bbox = min(bboxes, key=bboxes.get)

        if bbox:
            potentialbbox = track.init(color_image,bbox)
            print(potentialbbox)

            # for f in range(len(betweenFrames)):
            #     if potentialbbox is None:
            #         break
            #     potentialbbox = track.update(betweenFrames[f])
            #     print(potentialbbox)

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

            if collectFrames.value:
                betweenFrames.append(color_image)
            realCounter+=1
            frameNumber+=1

            # Finds the coordinate for the center of the screen
            center = (color_image.shape[1] / 2, color_image.shape[0] / 2)
            
            # run model if there is no current bounding box in another process
            if best_bounding_box[:] == [-1,-1,-1,-1]:
                if process is None or process.is_alive()==False:
                    collectFrames.value = True
                    process = Process(target=modelMulti,args=(color_image,confidence,threshold,best_bounding_box,track,model,betweenFrames,collectFrames,center))
                    process.start() 
                    realCounter=1

            else:
            # run model in another process every model_frequency frames
                if realCounter % model_frequency == 0:
                    # call model and initialize tracker
                    if process is None or process.is_alive()==False:
                        collectFrames.value = True
                        process = Process(target=modelMulti,args=(color_image,confidence,threshold,best_bounding_box,track,model,betweenFrames,collectFrames,center))
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
            if testing == False:
                z0 = cameraMethods.getDistFromArray(depth_image,best_bounding_box,gridSize)
                kalmanBox = [best_bounding_box[0],best_bounding_box[1],z0] # Put data into format the kalman filter asks for
                prediction = kalmanFilter.predict(kalmanBox) # figure out where to aim
            
                # send data to embedded
                hAngle, vAngle = angleFromCenter(prediction[1],prediction[0],center[0],center[1],horizontalFOV,verticalFOV) # send column,row since using array but calculating angle for image
                embedded_communication.send_output(hAngle, vAngle)

            # optional value for debugging/testing
            if not (on_next_frame is None) :
                on_next_frame(frameNumber, color_image, ([best_bounding_box[:]], [1])if best_bounding_box[:] != [-1,-1,-1,-1] else ([], []), (0,0))
            
        process.join() # make sure process is complete to avoid errors being thrown

    # return a list of the different main options
    return simple_synchronous, synchronous_with_tracker,multiprocessing_with_tracker
    

if __name__ == '__main__':
    # setup mains with real inputs/outputs
    import source.videostream._tests.get_live_video_frame as liveVideo
    camera = liveVideo.liveFeed()

    # Must send classes so multiprocessing is possible
    simple_synchronous, synchronous_with_tracker,multiprocessing_with_tracker = setup(
        get_frame = camera.get_live_video_frame, 
        modeling=test_modeling,
        tracker=test_tracking,
        aiming=test_aiming,
        testing = False
    )
    # TODO: CREATE INSTANCE OF AIMING CLASS WHERE IT INITIALIZES PIPELINE, THIS WILL BE THE BEGINNING OF AIMING INTEGRATION

    simple_synchronous()