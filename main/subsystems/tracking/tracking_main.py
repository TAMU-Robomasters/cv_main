# Imports the KCF tracker from OpenCV
import cv2 # alternative: from cv2 import TrackerMOSSE_create which is a way faster tracker with lower accuracy and can't tell when tracking fails

# local imports
from toolbox.image_tools import Image
from toolbox.globals import MACHINE, PATHS, PARAMETERS, COLOR_GREEN, print
class TrackingClass:
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
    def init(self,image, best_bounding_box):
        # creates the tracker and returns None if there are no bounding boxes to track
        self.tracker = cv2.TrackerKCF_create()
        print("Inside init for KCF Tracker.")
        
        # Attempts to start the tracker
        self.tracker.init(image, best_bounding_box)
        self.exists = True
        print("Tracker initialization successful.")
        
        # returns the tracked bounding box if tracker was successful, otherwise None
        return best_bounding_box

    # Updates the location of the object
    def update(self,image):
        # Attempts to update the object's location
        ok, location = self.tracker.update(image)
        print("Tracker is good?",ok)
        if ok == False:
            self.exists = False
        # Returns the location if the location was updated, otherwise None
        return location if ok else None
    def tracker_alive(self):
        return self.exists