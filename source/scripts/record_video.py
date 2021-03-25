import time
import pyrealsense2 as rs
import numpy as np
import sys
import cv2
# relative imports
from toolbox.video_tools import Video
from toolbox.image_tools import Image
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print
import source.modeling.modeling_main as modeling
import source.tracking.tracking_main as tracking
import source.videostream._tests.get_next_video_frame as nextVideoFrame

streamWidth = PARAMETERS['aiming']['stream_width']
streamHeight = PARAMETERS['aiming']['stream_height']
framerate = PARAMETERS['aiming']['stream_framerate']
gridSize = PARAMETERS['aiming']['grid_size']
frameAmount = PARAMETERS['videostream']['testing']['camera_frames']
timeRecord = PARAMETERS['videostream']['testing']['record_time']
colorVideoLocation = PATHS['record_video_output_color']
npyFramesLocation = PATHS['npy_frames']
confidence = PARAMETERS["model"]["confidence"]
threshold = PARAMETERS["model"]["threshold"]
model_frequency = PARAMETERS["model"]["frequency"]

pipeline = rs.pipeline()                                            
config = rs.config()                                                
config.enable_stream(rs.stream.depth, streamWidth, streamHeight, rs.format.z16, framerate)  
config.enable_stream(rs.stream.color, streamWidth, streamHeight, rs.format.bgr8, framerate) 
pipeline.start(config)

frame_dimensions = (streamWidth, streamHeight)
colorwriter = cv2.VideoWriter(colorVideoLocation, cv2.VideoWriter_fourcc(*'mp4v'), framerate, frame_dimensions)
t0 = time.time()
counter = 0

try:
    while (time.time()-t0)<timeRecord:
        counter+=1
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()

        if not color_frame or not depth_frame:
            continue

        color_image = np.asanyarray(color_frame.get_data())
        depth_image = np.asanyarray(depth_frame.get_data()).flatten()
        colorwriter.write(color_image)
        np.save(npyFramesLocation+str(counter)+"depth.dont_sync.npy",depth_image)

        print("FRAME ORIGINAL:",counter)
finally:
    colorwriter.release()
    pipeline.stop()

def distance(point_1: tuple, point_2: tuple):
    # Calculates the distance using Python spagettie
    distance = (sum((p1 - p2) ** 2.0 for p1, p2 in zip(point_1, point_2))) ** (1 / 2)
    # Returns the distance between two points
    return distance


model = modeling.modelingClass()
track = tracking.trackingClass()
colorVideo = nextVideoFrame.nextFromVideo(colorVideoLocation)
best_bounding_box = None
realCounter = 0
counter = 0

color_image = colorVideo.getFrame()
while color_image is not None:
    counter+=1
    realCounter+=1
    print("FRAME PROCESSING:",realCounter)
    np.save(npyFramesLocation+str(counter)+"color.dont_sync.npy",color_image.flatten())
    center = (color_image.shape[1] / 2, color_image.shape[0] / 2) # (x from columns/2, y from rows/2)

    if counter % model_frequency == 0 or (best_bounding_box is None):
        counter = 0
        boxes, confidences, classIDs, color_image = model.get_bounding_boxes(color_image, confidence, threshold)

        if len(boxes) != 0:
            # Makes a dictionary of bounding boxes using the bounding box as the key and its distance from the center as the value
            bboxes = {tuple(bbox): distance(center, (bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2)) for bbox in boxes}
            # Finds the centermost bounding box
            best_bounding_box = min(bboxes, key=bboxes.get)
            best_bounding_box = track.init(color_image,best_bounding_box)
    else:
        best_bounding_box = track.update(color_image)
    np.save(npyFramesLocation+str(realCounter)+"bbox.dont_sync.npy",np.array(best_bounding_box if best_bounding_box else [-1,-1,-1,-1]).flatten())
    color_image = colorVideo.getFrame()