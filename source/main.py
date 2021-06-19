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
horizontal_fov = PARAMETERS['aiming']['horizontal_fov']
vertical_fov = PARAMETERS['aiming']['vertical_fov']


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
    
    def angleFromCenter(xBboxCenter,yBboxCenter,xCamCenter,yCamCenter):
        """
        Returns the x and y angles between the center of the image and the center of a bounding box.

        We send xCamCenter and yCamCenter instead of importing 
        from info.yaml since recorded video footage could be different resolutions.

        Input: Bounding box and camera center components.
        Output: Horizontal and vertical angle in radians.
        """
        horizontal_angle = ((xBboxCenter-xCamCenter)/xCamCenter)*(horizontal_fov/2)
        vertical_angle = ((yBboxCenter-yCamCenter)/yCamCenter)*(vertical_fov/2)

        return math.radians(horizontal_angle),math.radians(vertical_angle)

    def updateCircularBuffers(x_circular_buffer,y_circular_buffer,prediction):
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
    
    def getOptimalBoundingBox(boxes,confidences,center):
        """
        Decide the single best bounding box to aim at using a score system.

        Input: All detected bounding boxes with their confidences and the center location of the image.
        Output: Best bounding box and its confidence.
        """

        best_bounding_box = boxes[0]
        best_score = 0
        cf = 0
        normalizationConstant = distance((center[0]*2,center[1]*2),(center[0],center[1])) # Find constant used to scale distance part of score to 1

        # Sequentially iterate through all bounding boxes
        for i in range(len(boxes)):
            bbox = boxes[i]
            score = (1 - distance(center,(bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2))/ normalizationConstant) + confidences[i] # Compute score using distance and confidence

            # Make current box the best if its score is the best so far
            if score > best_score:
                best_bounding_box = boxes[i]
                best_score = score
                cf = confidences[i]
        
        return best_bounding_box, cf
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
        model = modeling.modelingClass() # Create instance of modeling
        horizontal_angle = vertical_angle = x_std = y_std = depth_amount = pixel_diff = phi = cf = shoot = 0 # Initialize constants as "globals"
        buffer_size = 10

        # Create two circular buffers to store predicted shooting locations (used to ensure we are locked on a target)
        x_circular_buffer = collections.deque(maxlen=buffer_size)
        y_circular_buffer = collections.deque(maxlen=buffer_size)

        while True:
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

            # run the model
            boxes, confidences, class_ids, color_image = model.get_bounding_boxes(color_image, confidence, threshold, filter_team_color)

            # Finds the coordinate for the center of the screen
            center = (color_image.shape[1] / 2, color_image.shape[0] / 2) # (x from columns/2, y from rows/2)

            # Continue control logic if we detected atleast a single bounding box
            if len(boxes)!=0:
                # Makes a dictionary of bounding boxes using the bounding box as the key and its distance from the center as the value
                # bboxes = {tuple(bbox): distance(center, (bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2)) for bbox in boxes}
                # best_bounding_box = min(bboxes, key=bboxes.get) # Finds the centermost bounding box

                best_bounding_box, cf = getOptimalBoundingBox(boxes,confidences,center)

                prediction = [best_bounding_box[0]+best_bounding_box[2]/2,best_bounding_box[1]+best_bounding_box[3]/2] # Location to shoot [xObjCenter, yObjCenter]
                print("Best Bounding Box",best_bounding_box)
                print("Prediction is:",prediction)

                depth_amount = cameraMethods.getDistFromArray(depth_image,best_bounding_box) # Find depth from camera to robot
                bboxY = prediction[1]
                # phi = embedded_communication.getPhi()
                # if phi:
                pixel_diff = 0 # just here in case we comment out the next line
                # pixel_diff = -(cameraMethods.bulletDropCompensation(depth_image,best_bounding_box,depth_amount,center,phi))
                pixel_diff = cameraMethods.bulletOffsetCompensation(depth_amount)
                if pixel_diff is None:
                    x_circular_buffer.clear()
                    y_circular_buffer.clear()
                    pixel_diff = 0
                    
                
                prediction[1] -= pixel_diff

                x_std, y_std = updateCircularBuffers(x_circular_buffer,y_circular_buffer,prediction) # Update buffers and measures of accuracy
                horizontal_angle, vertical_angle = angleFromCenter(prediction[0],center[1]*2-prediction[1],center[0],center[1]) # Determine angles to turn by in both x,y components
                print("Angles calculated are horizontal_angle:",horizontal_angle,"and vertical_angle:",vertical_angle)

                # Send embedded the angles to turn to and the accuracy, make accuracy terrible if we dont have enough data in buffer 
                if depth_amount < 1 or depth_amount > 3.5:
                    x_circular_buffer.clear()
                    y_circular_buffer.clear()
                    shoot = embedded_communication.send_output(horizontal_angle, vertical_angle, 255, 255)
                elif len(x_circular_buffer) == buffer_size:
                    shoot = embedded_communication.send_output(horizontal_angle, vertical_angle,x_std,y_std)
                else:
                    shoot = embedded_communication.send_output(horizontal_angle, vertical_angle,255,255)

                # If gui is enabled then draw bounding boxes around the selected robot
                if with_gui:
                    cv2.rectangle(color_image, (best_bounding_box[0], best_bounding_box[1]), (best_bounding_box[0] + best_bounding_box[2], best_bounding_box[1] + best_bounding_box[3]), (255,0,0), 2)
            else:
                # Clears buffers since no robots detected
                x_circular_buffer.clear()
                y_circular_buffer.clear()
                # embedded_communication.send_output(0, 0, 255, 255) # Tell embedded to stay still 
                print("No Bounding Boxes Found")

            # Display time taken for single iteration of loop
            iteration_time = time.time()-t
            print('Processing frame',frame_number,'took',iteration_time,"seconds for model only\n")

            # Show live feed is gui is enabled
            if with_gui:
                # Set cv2 text writing constants
                font = cv2.FONT_HERSHEY_SIMPLEX 
                bottomLeftCornerOfText = (10,10) 
                fontScale = .7
                fontColor = (255,255,255) 
                lineType = 2

                cv2.putText(color_image,"horizontal_angle: "+str(np.round(horizontal_angle,2)), (30,50) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"vertical_angle: "+str(np.round(vertical_angle,2)), (30,100) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"depth_amount: "+str(np.round(depth_amount,2)), (30,150) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"pixel_diff: "+str(np.round(pixel_diff,2)), (30,200) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"xSTD: "+str(np.round(x_std,2)), (30,250) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"ySTD: "+str(np.round(y_std,2)), (30,300) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"confidence: "+str(np.round(cf,2)), (30,350) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"FPS: "+str(np.round(1/iteration_time,2)), (30,400) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"Shoot: "+str(shoot), (30,450) , font, fontScale,fontColor,lineType)


                if phi:
                    cv2.putText(color_image,"Phi: "+str(np.round(phi,2)), (30,450) , font, fontScale,fontColor,lineType)

                cv2.imshow("feed",color_image)
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
        frameNumber = 0
        cf = 0
        best_bounding_box = None
        buffer_size = 10

        # Create two circular buffers to store predicted shooting locations (used to ensure we are locked on a target)
        x_circular_buffer = collections.deque(maxlen=buffer_size)
        y_circular_buffer = collections.deque(maxlen=buffer_size)
        
        # initialize model and tracker classes
        track = tracker.trackingClass()
        model = modeling.modelingClass()
        kalmanFilter = None

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
                if video_output and frameNumber % record_interval == 0:
                    print("Saving Frame",frameNumber)
                    video_output.write(color_image)
            else:
                if frame is None: # If there is no more frames then end method
                    break
                if isinstance(frame,int): # If an int was returned we simply had a faulty frame
                    continue
                color_image = frame


            frameNumber+=1
            counter+=1

            center = (color_image.shape[1] / 2, color_image.shape[0] / 2) # Finds the coordinate for the center of the screen
            
            # Run model every model_frequency frames or whenever the tracker fails
            if counter % model_frequency == 0 or (best_bounding_box is None):
                counter=1
                best_bounding_box = None
                boxes, confidences, class_ids, color_image = model.get_bounding_boxes(color_image, confidence, threshold, filter_team_color) # Call model

                # Continue control logic if we detected atleast a single bounding box
                if len(boxes) != 0:
                    # Makes a dictionary of bounding boxes using the bounding box as the key and its distance from the center as the value
                    # bboxes = {tuple(bbox): distance(center, (bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2)) for bbox in boxes}
                    # Finds the centermost bounding box
                    # best_bounding_box = min(bboxes, key=bboxes.get)

                    # Get the best bounding box and initialize the tracker
                    best_bounding_box, cf = getOptimalBoundingBox(boxes,confidences,center)
                    if best_bounding_box:
                        best_bounding_box = track.init(color_image,tuple(best_bounding_box))
                        print("Now Tracking a New Object.")

                        # Reinitialize kalman filters
                        if kalman_filters:
                            kalmanFilter = aiming.Filter(modelFPS)
                            print("Reinitialized Kalman Filter.")
            else:
                best_bounding_box = track.update(color_image) # Get new position of bounding box from tracker

            horizontal_angle = vertical_angle = x_std = y_std = depth_amount = bboxY = pixel_diff = bboxHeight = phi = 0 # Initialize constants as "globals"

            # Continue control logic if we detected atleast a single bounding box
            if best_bounding_box is not None:
                prediction = [best_bounding_box[0]+best_bounding_box[2]/2,best_bounding_box[1]+best_bounding_box[3]/2] # Location to shoot [xObjCenter, yObjCenter]
                bboxHeight = best_bounding_box[3]
                print("Prediction is:",prediction)

                # Comment this if branch out in case kalman filters doesn't work
                # if kalman_filters:
                #     prediction[1] += cameraMethods.getBulletDropPixels(depth_image,best_bounding_box)
                    # kalmanBox = [prediction[0],prediction[1],z0] # Put data into format the kalman filter asks for
                    # prediction = kalmanFilter.predict(kalmanBox, frame) # figure out where to aim, returns (xObjCenter, yObjCenter)
                    # print("Kalman Filter updated Prediction to:",prediction)

                depth_amount = cameraMethods.getDistFromArray(depth_image,best_bounding_box) # Find depth from camera to robot
                bboxY = prediction[1]

                pixel_diff = cameraMethods.bulletOffsetCompensation(depth_amount)
                if pixel_diff is None:
                    x_circular_buffer.clear()
                    y_circular_buffer.clear()
                    pixel_diff = 0

                prediction[1] -= pixel_diff

                x_std, y_std = updateCircularBuffers(x_circular_buffer,y_circular_buffer,prediction) # Update buffers and measures of accuracy
                horizontal_angle, vertical_angle = angleFromCenter(prediction[0],prediction[1],center[0],center[1]) # Determine angles to turn by in both x,y components
                print("Angles calculated are horizontal_angle:",horizontal_angle,"and vertical_angle:",vertical_angle)

                # Send embedded the angles to turn to and the accuracy, make accuracy terrible if we dont have enough data in buffer                
                if depth_amount < 1 or depth_amount > 3.5:
                    x_circular_buffer.clear()
                    y_circular_buffer.clear()
                    embedded_communication.send_output(horizontal_angle, vertical_angle, 255, 255) # Tell embedded to stay still 
                elif len(x_circular_buffer) == buffer_size:
                    embedded_communication.send_output(horizontal_angle, vertical_angle,x_std,y_std)
                else:
                    embedded_communication.send_output(horizontal_angle, vertical_angle,255,255)
                # If gui is enabled then draw bounding boxes around the selected robot
                if with_gui:
                    cv2.rectangle(color_image, (int(best_bounding_box[0]), int(best_bounding_box[1])), (int(best_bounding_box[0]) + int(best_bounding_box[2]), int(best_bounding_box[1]) + int(best_bounding_box[3])), (255,0,0), 2)
            else:
                # Clears buffers since no robots detected
                x_circular_buffer.clear()
                y_circular_buffer.clear()

                # embedded_communication.send_output(0, 0, 255, 255) # Tell embedded to stay still and not shoot
                print("No Bounding Boxes Found")

            # Display time taken for single iteration of loop
            iteration_time = time.time() - t
            print('Processing frame',frameNumber,'took',iteration_time,"seconds for model+tracker")

            # Show live feed is gui is enabled
            if with_gui:
                # Set cv2 text writing constants
                font = cv2.FONT_HERSHEY_SIMPLEX 
                bottomLeftCornerOfText = (10,10) 
                fontScale = .7
                fontColor = (255,255,255) 
                lineType = 2

                # Draw text on image
                cv2.putText(color_image,"horizontal_angle: "+str(np.round(horizontal_angle,2)), (30,50) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"vertical_angle: "+str(np.round(vertical_angle,2)), (30,100) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"depth_amount: "+str(np.round(depth_amount,2)), (30,150) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"pixel_diff: "+str(np.round(pixel_diff,2)), (30,200) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"xSTD: "+str(np.round(x_std,2)), (30,250) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"ySTD: "+str(np.round(y_std,2)), (30,300) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"confidence: "+str(np.round(cf,2)), (30,350) , font, fontScale,fontColor,lineType)
                cv2.putText(color_image,"FPS: "+str(np.round(1/iteration_time,2)), (30,400) , font, fontScale,fontColor,lineType)

                if phi:
                    cv2.putText(color_image,"phi: "+str(np.round(phi,2)), (30,450) , font, fontScale,fontColor,lineType)

                cv2.imshow("feed",color_image)
                cv2.waitKey(10)

            # Optional value for debugging/testing for video footage only
            if not (on_next_frame is None):
                on_next_frame(frameNumber, color_image, ([best_bounding_box], [1])if best_bounding_box else ([], []),(horizontal_angle,vertical_angle))
                
    
    def modelMulti(color_image,confidence,threshold,best_bounding_box,track,model,betweenFrames,collectFrames,center):
        # Run the model and update best bounding box to the new bounding box if it exists, otherwise keep tracking the old bounding box
        boxes, confidences, class_ids, color_image = model.get_bounding_boxes(color_image, confidence, threshold)
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
                horizontal_angle, vertical_angle = angleFromCenter(prediction[0],prediction[1],center[0],center[1],horizontalFOV,verticalFOV) # (xObj,yObj,xCam/2,yCam/2,hFov,vFov)
                embedded_communication.send_output(horizontal_angle, vertical_angle)

            # optional value for debugging/testing
            if not (on_next_frame is None) :
                on_next_frame(frameNumber, color_image, ([best_bounding_box[:]], [1])if best_bounding_box[:] != [-1,-1,-1,-1] else ([], []), (0,0))
            
        process.join() # make sure process is complete to avoid errors being thrown

    # return a list of the different main options
    return simple_synchronous, synchronous_with_tracker,multiprocessing_with_tracker
    
def beginVideoRecording():
    """
    Run live video recording using nvenc.

    Input: None
    Output: Video object to add frames too.
    """

    # Setup video output path based on date and counter
    c=1
    filePath = colorVideoLocation.replace(".dont-sync",datetime.datetime.now().strftime("%Y-%m-%d")+"_"+str(c)+".dont-sync")
    while os.path.isfile(filePath):
        c+=1
        filePath = colorVideoLocation.replace(".dont-sync",datetime.datetime.now().strftime("%Y-%m-%d")+"_"+str(c)+".dont-sync")

    # Start up video output
    gst_out = "appsrc ! video/x-raw, format=BGR ! queue ! videoconvert ! video/x-raw,format=BGRx ! nvvidconv ! nvv4l2h264enc ! h264parse ! matroskamux ! filesink location="+filePath
    video_output = cv2.VideoWriter(gst_out, cv2.CAP_GSTREAMER, 0, float(framerate), (int(streamWidth), int(streamHeight)))
    if not video_output.isOpened():
        print("Failed to open output")

    return video_output

if __name__ == '__main__':
    # Relative imports here since pyrealsense requires camera to be plugged in or code will crash
    import source.videostream._tests.get_live_video_frame as liveVideo
    import source.aiming.filter as test_aiming

    camera = liveVideo.liveFeed()
    video_output = None

    try:
        # Setup video recording configuration if enabled
        if record_interval>0:
            video_output = beginVideoRecording()

        # Must send classes so multiprocessing is possible
        simple_synchronous, synchronous_with_tracker,multiprocessing_with_tracker = setup(
            get_frame = camera.get_live_video_frame, 
            modeling = test_modeling,
            tracker = test_tracking,
            aiming = test_aiming,
            live_camera = True,
            kalman_filters = False,
            with_gui = True,
            filter_team_color = False,
            video_output = video_output
        )

        simple_synchronous() # CHANGE THIS LINE FOR DIFFERENT MAIN METHODS

    finally:
        # Save video output
        if video_output:
            print("Saving Recorded Video")
            video_output.release()
            print("Finished Saving Video")