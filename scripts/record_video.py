import time
import pyrealsense2 as rs
import numpy as np
import sys
import cv2
import os
# project imports
from toolbox.video_tools import Video
from toolbox.image_tools import Image
from toolbox.globals import path_to, config, print
import subsystems.modeling.modeling_main as modeling
import subsystems.tracking.tracking_main as tracking
import subsystems.videostream._tests.get_next_video_frame as next_video_frame

os.system("mkdir -p ./source/scripts")

stream_width         = config.aiming.stream_width
stream_height        = config.aiming.stream_height
framerate            = config.aiming.stream_framerate
grid_size            = config.aiming.grid_size
time_record          = config.videostream.testing.record_time
confidence           = config.model.minimum_confidence
threshold            = config.model.threshold
model_frequency      = config.model.frequency
color_video_location = path_to.record_video_output_color
npy_frames_location  = path_to.npy_frames

os.system("mkdir -p "+npy_frames_location)
os.system("rm "+npy_frames_location+"/*")

pipeline = rs.pipeline()                                            
config = rs.config()                                                
config.enable_stream(rs.stream.depth, stream_width, stream_height, rs.format.z16, framerate)  
config.enable_stream(rs.stream.color, stream_width, stream_height, rs.format.bgr8, framerate) 
pipeline.start(config)

frame_dimensions = (stream_width, stream_height)
colorwriter = cv2.VideoWriter(color_video_location, cv2.VideoWriter_fourcc(*'mp4v'), framerate, frame_dimensions)
t0 = time.time()
counter = 0

try:
    while (time.time()-t0)<time_record:
        counter+=1
        frames = pipeline.wait_for_frames()
        color_frame = frames.get_color_frame()
        depth_frame = frames.get_depth_frame()

        if not color_frame or not depth_frame:
            continue

        color_image = np.asanyarray(color_frame.get_data())
        depth_image = np.asanyarray(depth_frame.get_data()).flatten()
        colorwriter.write(color_image)
        np.save(npy_frames_location+"/"+str(counter)+"depth.do_not_sync.npy",depth_image)
    
        print("FRAME ORIGINAL:",counter)
finally:
    colorwriter.release()
    pipeline.stop()

def distance(point_1: tuple, point_2: tuple):
    # Calculates the distance using Python spagettie
    distance = (sum((p1 - p2) ** 2.0 for p1, p2 in zip(point_1, point_2))) ** (1 / 2)
    # Returns the distance between two points
    return distance


model = modeling.ModelingClass()
track = tracking.TrackingClass()
color_video = next_video_frame.NextFromVideo(color_video_location)
best_bounding_box = None
real_counter = 0
counter = 0

color_image = color_video.get_frame()
while color_image is not None:
    counter+=1
    real_counter+=1
    print("FRAME PROCESSING:",real_counter)
    np.save(npy_frames_location+"/"+str(real_counter)+"color.do_not_sync.npy",color_image.flatten())
    center = (color_image.shape[1] / 2, color_image.shape[0] / 2) # (x from columns/2, y from rows/2)

    if counter % model_frequency == 0 or (best_bounding_box is None):
        counter = 0
        best_bounding_box = None
        boxes, confidences, class_ids, color_image = model.get_bounding_boxes(color_image, threshold)
        print("MODEL")
        if len(boxes) != 0:
            print("FOUND BOX")
            # Makes a dictionary of bounding boxes using the bounding box as the key and its distance from the center as the value
            bboxes = {tuple(bbox): distance(center, (bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2)) for bbox in boxes}
            # Finds the centermost bounding box
            best_bounding_box = min(bboxes, key=bboxes.get)
            best_bounding_box = track.init(color_image,best_bounding_box)
    else:
        best_bounding_box = track.update(color_image)
        print("TRACKER")
    np.save(npy_frames_location+"/"+str(real_counter)+"bbox.do_not_sync.npy",np.array(best_bounding_box if best_bounding_box else [-1,-1,-1,-1]).flatten())
    color_image = color_video.get_frame()