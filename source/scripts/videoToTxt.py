import time
import numpy as np
import sys
import cv2

# relative imports
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print
import source.modeling.modeling_main as modeling
import source.tracking.tracking_main as tracking
import source.videostream._tests.get_next_video_frame as nextVideoFrame

confidence = PARAMETERS["model"]["confidence"]
threshold = PARAMETERS["model"]["threshold"]
pathColor = PATHS["record_video_output_color"]
pathDepth = PATHS["record_video_output_depth"]
pathTxt = PATHS["color_depth"]

file = open(pathTxt,"w")
model = modeling.modelingClass()
track = tracking.trackingClass()
colorVideo = nextVideoFrame.nextFromVideo(pathColor)
depthText = open(pathDepth,'r')
best_bounding_box = None
counter = 0

def distance(point_1: tuple, point_2: tuple):
    # Calculates the distance using Python spagettie
    distance = (sum((p1 - p2) ** 2.0 for p1, p2 in zip(point_1, point_2))) ** (1 / 2)
    # Returns the distance between two points
    return distance

color_image = colorVideo.getFrame()
while color_image is not None:
    content = ""
    for row in color_image:
        for col in row:
            content += str(col[0])+" " + str(col[1])+" " + str(col[2])+" "
    file.write(content+"\n")

    file.write(depthText.readline())

    center = (color_image.shape[1] / 2, color_image.shape[0] / 2) # (x from columns/2, y from rows/2)
    counter+=1

    if counter % 100 == 0 or (best_bounding_box is None):
        counter=1
        boxes, confidences, classIDs, color_image = model.get_bounding_boxes(color_image, confidence, threshold)

        if len(boxes) != 0:
            # Makes a dictionary of bounding boxes using the bounding box as the key and its distance from the center as the value
            bboxes = {tuple(bbox): distance(center, (bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2)) for bbox in boxes}
            # Finds the centermost bounding box
            best_bounding_box = min(bboxes, key=bboxes.get)
            best_bounding_box = track.init(color_image,best_bounding_box)
    else:
        best_bounding_box = track.update(color_image)

    if best_bounding_box is None:
        file.write("-1 -1 -1 -1\n")
    else:
        file.write(str(best_bounding_box[0])+" "+str(best_bounding_box[1])+" "+str(best_bounding_box[2])+" "+str(best_bounding_box[3])+"\n")
file.close()