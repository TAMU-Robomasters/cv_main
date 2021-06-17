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
import math
import time
import datetime
import collections

# relative imports
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print
from source.embedded_communication.embedded_main import embedded_communication
import source.modeling._tests.test_modeling as test_modeling
import source.tracking._tests.test_tracking as test_tracking
import source.aiming.depth_camera as cameraMethods

# import parameters from the info.yaml file
confidence = PARAMETERS["model"]["confidence"]
threshold = PARAMETERS["model"]["threshold"]
model_frequency = PARAMETERS["model"]["frequency"]
grabFrame = PARAMETERS['videostream']['testing']['grab_frame']
modelFPS = PARAMETERS['aiming']['model_fps']
gridSize = PARAMETERS['aiming']['grid_size']
horizontalFOV = PARAMETERS['aiming']['horizontal_fov']
verticalFOV = PARAMETERS['aiming']['vertical_fov']
withGUI = PARAMETERS['testing']['open_each_frame']
streamWidth = PARAMETERS['aiming']['stream_width']
streamHeight = PARAMETERS['aiming']['stream_height']
framerate = PARAMETERS['aiming']['stream_framerate']
colorVideoLocation = PATHS['record_video_output_color']
record_interval = PARAMETERS['videostream']['testing']['record_interval']

def setup(
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
        videoOutput = None
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
        return math.radians(hAngle),math.radians(vAngle)
    
    # 
    # option #1
    #
    def simple_synchronous():
        """
        this function is the most simple version of CV
        - no tracking
        - no multiprocessing/async/multithreading
        - no kalman filters since we need to track for that to be possible
        """

        frameNumber = 0 # used for on_next_frame
        model = modeling.modelingClass() # create instance of modeling

        while True:
            t = time.time()
            frame = get_frame()  
            color_image = None           
            depth_image = None

            if live_camera:
                color_frame = frame.get_color_frame()
                color_image = np.asanyarray(color_frame.get_data()) 
                depth_frame = frame.get_depth_frame() 
                depth_image = np.asanyarray(depth_frame.get_data()) 

                if videoOutput and frameNumber % record_interval == 0:
                    print("Saving Frame",frameNumber)
                    videoOutput.write(color_image)
            else:
                if frame is None:
                    break
                if isinstance(frame,int):
                    continue
                color_image = frame

            frameNumber+=1

            # run the model
            boxes, confidences, classIDs, color_image = model.get_bounding_boxes(color_image, confidence, threshold, filter_team_color)

            # Finds the coordinate for the center of the screen
            center = (color_image.shape[1] / 2, color_image.shape[0] / 2) # (x from columns/2, y from rows/2)
            hAngle = None
            vAngle = None

            if len(boxes)!=0:
                # Makes a dictionary of bounding boxes using the bounding box as the key and its distance from the center as the value
                bboxes = {tuple(bbox): distance(center, (bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2)) for bbox in boxes}
                # Finds the centermost bounding box
                best_bounding_box = min(bboxes, key=bboxes.get)

                prediction = [best_bounding_box[0]+best_bounding_box[2]/2,center[1]*2-best_bounding_box[1]+best_bounding_box[3]/2] # location to shoot [xObjCenter, yObjCenter]
                print("Prediction is:",prediction)


                hAngle, vAngle = angleFromCenter(prediction[0],prediction[1],center[0],center[1],horizontalFOV,verticalFOV) # (xObj,yObj,xCam/2,yCam/2,hFov,vFov) and returns angles in radians
                print("Angles calculated are hAngle:",hAngle,"and vAngle:",vAngle)
                embedded_communication.send_output(hAngle, vAngle)

                if with_gui:
                    cv2.rectangle(color_image, (best_bounding_box[0], best_bounding_box[1]), (best_bounding_box[0] + best_bounding_box[2], best_bounding_box[1] + best_bounding_box[3]), (255,0,0), 2)
            else:
                embedded_communication.send_output(0, 0)
                print("No Bounding Boxes Found")

            if with_gui:
                cv2.imshow("feed",color_image)
                cv2.waitKey(10)

            # cv2.imwrite("here.jpg",color_image)

            iterationTime = time.time()-t
            print('Processing frame',frameNumber,'took',iterationTime,"seconds for model only\n")

            # optional value for debugging/testing for video footage only
            if not (on_next_frame is None):
                on_next_frame(frameNumber, color_image, (boxes, confidences), (hAngle,vAngle))

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

        counter = 1
        frameNumber = 0 # used for on_next_frame
        best_bounding_box = None
        xCircularBuffer = collections.deque(maxlen=10)
        yCircularBuffer = collections.deque(maxlen=10)
        cf = 0
        
        # initialize model and tracker classes
        track = tracker.trackingClass()
        model = modeling.modelingClass()
        kalmanFilter = None

        while True: # counts up infinitely starting at 0
            # grabs frame and ends loop if we reach the last one
            print()
            t = time.time()
            frame = get_frame()  
            color_image = None           
            depth_image = None

            if live_camera:
                color_frame = frame.get_color_frame()
                color_image = np.asanyarray(color_frame.get_data()) 
                depth_frame = frame.get_depth_frame() 
                depth_image = np.asanyarray(depth_frame.get_data()) 

                if videoOutput and frameNumber % record_interval == 0:
                    print("Saving Frame",frameNumber)
                    videoOutput.write(color_image)
            else:
                if frame is None:
                    break
                if isinstance(frame,int):
                    continue
                color_image = frame

            frameNumber+=1
            counter+=1

            # Finds the coordinate for the center of the screen
            center = (color_image.shape[1] / 2, color_image.shape[0] / 2) # (x from columns/2, y from rows/2)
            
            # run model every model_frequency frames or whenever the tracker fails
            if counter % model_frequency == 0 or (best_bounding_box is None):
                counter=1
                best_bounding_box = None
                # call model
                boxes, confidences, classIDs, color_image = model.get_bounding_boxes(color_image, confidence, threshold,filter_team_color)
                if len(boxes) != 0:
                    # Makes a dictionary of bounding boxes using the bounding box as the key and its distance from the center as the value
                    # bboxes = {tuple(bbox): distance(center, (bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2)) for bbox in boxes}
                    # Finds the centermost bounding box
                    # best_bounding_box = min(bboxes, key=bboxes.get)

                    best_bounding_box = boxes[0]
                    best_score = 0
                    for i in range(len(boxes)):
                        bbox = boxes[i]
                        score = (1 - distance(center,(bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2))/ 487) + confidences[i]
                        cf = confidences[i]
                        if score > best_score:
                            best_bounding_box = boxes[i]
                            best_score = score


                    best_bounding_box = track.init(color_image,tuple(best_bounding_box))

                    print("Now Tracking a New Object.")
                    if kalman_filters:
                        kalmanFilter = aiming.Filter(modelFPS)
                        print("Reinitialized Kalman Filter.")
            else:
                best_bounding_box = track.update(color_image)

            hAngle = vAngle = xstd = ystd = depthAmount = bboxY = pixelDiff = bboxHeight = 0

            if best_bounding_box is not None:
                prediction = [best_bounding_box[0]+best_bounding_box[2]/2,center[1]*2-best_bounding_box[1]-best_bounding_box[3]/2] # xObjCenter, yObjCenter
                bboxHeight = best_bounding_box[3]
                print("Prediction is:",prediction)

                # Comment this if branch out in case kalman filters doesn't work
                # if kalman_filters:
                #     prediction[1] += cameraMethods.getBulletDropPixels(depth_image,best_bounding_box)
                    # kalmanBox = [prediction[0],prediction[1],z0] # Put data into format the kalman filter asks for
                    # prediction = kalmanFilter.predict(kalmanBox, frame) # figure out where to aim, returns (xObjCenter, yObjCenter)
                    # print("Kalman Filter updated Prediction to:",prediction)

                depthAmount = cameraMethods.getDistFromArray(depth_image,best_bounding_box)
                bboxY = prediction[1]
                pixelDiff = cameraMethods.bulletDrop(depthAmount)
                prediction[1] += pixelDiff

                xCircularBuffer.append(prediction[0])
                yCircularBuffer.append(prediction[1])
                xstd = np.std(xCircularBuffer)
                ystd = np.std(yCircularBuffer)

                # send data to embedded
                hAngle, vAngle = angleFromCenter(prediction[0],prediction[1],center[0],center[1],horizontalFOV,verticalFOV) # (xObj,yObj,xCam/2,yCam/2,hFov,vFov) and returns angles in radians
                print("Angles calculated are hAngle:",hAngle,"and vAngle:",vAngle)
                embedded_communication.send_output(hAngle, vAngle,xstd,ystd)

                if with_gui:
                    cv2.rectangle(color_image, (int(best_bounding_box[0]), int(best_bounding_box[1])), (int(best_bounding_box[0]) + int(best_bounding_box[2]), int(best_bounding_box[1]) + int(best_bounding_box[3])), (255,0,0), 2)
            else:
                xCircularBuffer.append(255)
                yCircularBuffer.append(255)
                xstd = np.std(xCircularBuffer)
                ystd = np.std(yCircularBuffer)
                embedded_communication.send_output(0, 0,255,255)

                print("No Bounding Boxes Found")

            # optional value for debugging/testing
            iterationTime = time.time() - t
            print('Processing frame',frameNumber,'took',iterationTime,"seconds for model+tracker")

            if with_gui:
                font = cv2.FONT_HERSHEY_SIMPLEX 
                bottomLeftCornerOfText = (10,10) 
                fontScale = .7
                fontColor = (255,255,255) 
                lineType = 2

                cv2.putText(color_image,"hAngle: "+str(np.round(hAngle,2)), (30,50) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"vAngle: "+str(np.round(vAngle,2)), (30,100) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"depthAmount: "+str(np.round(depthAmount,2)), (30,150) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"bboxY: "+str(np.round(bboxY,2)), (30,200) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"pixelDiff: "+str(np.round(pixelDiff,2)), (30,250) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"bboxHeight: "+str(np.round(bboxHeight,2)), (30,400) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"xSTD: "+str(np.round(xstd,2)), (30,300) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"ySTD: "+str(np.round(ystd,2)), (30,350) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"confidence: "+str(np.round(cf,2)), (30,400) , font, fontScale,fontColor,lineType)


                cv2.imshow("feed",color_image)
                cv2.waitKey(10)

            # cv2.imwrite("here.jpg",color_image)

            if not (on_next_frame is None):
                on_next_frame(frameNumber, color_image, ([best_bounding_box], [1])if best_bounding_box else ([], []),(hAngle,vAngle))
                
    
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
            center = (color_image.shape[1] / 2, color_image.shape[0] / 2) # (x from columns/2, y from rows/2)
            
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
                hAngle, vAngle = angleFromCenter(prediction[0],prediction[1],center[0],center[1],horizontalFOV,verticalFOV) # (xObj,yObj,xCam/2,yCam/2,hFov,vFov)
                embedded_communication.send_output(hAngle, vAngle)

            # optional value for debugging/testing
            if not (on_next_frame is None) :
                on_next_frame(frameNumber, color_image, ([best_bounding_box[:]], [1])if best_bounding_box[:] != [-1,-1,-1,-1] else ([], []), (0,0))
            
        process.join() # make sure process is complete to avoid errors being thrown

    # return a list of the different main options
    return simple_synchronous, synchronous_with_tracker,multiprocessing_with_tracker
    
def beginVideoRecording():
        c=1
        filePath = colorVideoLocation.replace(".dont-sync",datetime.datetime.now().strftime("%Y-%m-%d")+"_"+str(c)+".dont-sync")
        while os.path.isfile(filePath):
            c+=1
            filePath = colorVideoLocation.replace(".dont-sync",datetime.datetime.now().strftime("%Y-%m-%d")+"_"+str(c)+".dont-sync")

        gst_out = "appsrc ! video/x-raw, format=BGR ! queue ! videoconvert ! video/x-raw,format=BGRx ! nvvidconv ! nvv4l2h264enc ! h264parse ! matroskamux ! filesink location="+filePath
        videoOutput = cv2.VideoWriter(gst_out, cv2.CAP_GSTREAMER, 0, float(framerate), (int(streamWidth), int(streamHeight)))
        if not videoOutput.isOpened():
            print("Failed to open output")

        return videoOutput

if __name__ == '__main__':
    # setup mains with real inputs/outputs
    import source.videostream._tests.get_live_video_frame as liveVideo
    import source.aiming.filter as test_aiming

    camera = liveVideo.liveFeed()
    videoOutput = None

    # TODO: CHECK INFINITELY UNTIL EMBEDDED SAYS MATCH STARTED HERE

    try:
        if record_interval>0:
            videoOutput = beginVideoRecording()

        # Must send classes so multiprocessing is possible
        simple_synchronous, synchronous_with_tracker,multiprocessing_with_tracker = setup(
            get_frame = camera.get_live_video_frame, 
            modeling = test_modeling,
            tracker = test_tracking,
            aiming = test_aiming,
            live_camera = True,
            kalman_filters = False,
            with_gui = True,
            filter_team_color = True,
            videoOutput = videoOutput
        )

        synchronous_with_tracker() # CHANGE THIS LINE FOR DIFFERENT MAIN METHODS

    finally:
        if videoOutput:
            print("Saving Recorded Video")
            videoOutput.release()
            print("Finished Saving Video")