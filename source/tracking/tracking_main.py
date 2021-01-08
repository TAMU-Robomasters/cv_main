# Imports the KCF tracker from OpenCV
import cv2 # alternative: from cv2 import TrackerMOSSE_create which is a way faster tracker with lower accuracy and can't tell when tracking fails

# local imports
from toolbox.image_tools import Image
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, COLOR_GREEN, print
class trackingClass:
    def __init__(self):
        self.tracker =  None
    # Finds the absolute distance between two points
    def distance(self,point_1: tuple, point_2: tuple):
        # Calculates the distance using Python spagettie
        distance = (sum((p1 - p2) ** 2.0 for p1, p2 in zip(point_1, point_2))) ** (1 / 2)
        # Returns the distance between two points
        return distance
    # Starts tracking the object surrounded by the bounding box in the image
    # bbox is [x, y, width, height]
    def init(self,image, bboxes):
        # creates the tracker and returns None if there are no bounding boxes to track
        self.tracker = cv2.TrackerKCF_create()
        print("inside init for KCF")
        print(bboxes)
        if len(bboxes) == 0:
            return None
        # Finds the coordinate for the center of the screen
        center = (image.shape[1] / 2, image.shape[0] / 2)

        # Makes a dictionary of bounding boxes using the bounding box as the key and its distance from the center as the value
        bboxes = {tuple(bbox): self.distance(center, (bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2)) for bbox in bboxes}

        # Finds the centermost bounding box
        bbox = min(bboxes, key=bboxes.get)

        # Attempts to start the tracker
        self.tracker.init(image, bbox)
        self.exists = True
        print("TRACKER INIT")
        
        # returns the tracked bounding box if tracker was successful, otherwise None
        return bbox

    # Updates the location of the object
    def update(self,image):
        # Attempts to update the object's location
        ok, location = self.tracker.update(image)
        print("TRACKER CONTINUE",ok)
        if ok == False:
            self.exists = False
        # Returns the location if the location was updated, otherwise None
        return location if ok else None
    def trackerAlive(self):
        return self.exists