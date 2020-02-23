# Imports the MOSSE tracker from OpenCV
from cv2 import TrackerMOSSE_create # alternative: from cv2 import TrackerCSRT_create
# Import the function to draw bbox from OpenCV
from cv2 import rectangle
from toolbox.image_tools import Image
from toolbox.globals import COLOR_GREEN

# Creates the MOSSE tracker object
tracker = TrackerMOSSE_create()

# Finds the absolute distance between two points
def distance(point_1: tuple, point_2: tuple):
    # Calculates the distance using Python spagettie
    distance = (sum((p1 - p2) ** 2.0 for p1, p2 in zip(point_1, point_2))) ** (1 / 2)
    # Returns the distance between two points
    return distance

# Starts tracking the object surrounded by the bounding box in the image
# bbox is [x, y, width, height]
def init(image, bboxes, video = []):
    global tracker
    tracker = TrackerMOSSE_create()
    print("inside init")
    print(bboxes)
    if len(bboxes) == 0:
        return False
    # Finds the coordinate for the center of the screen
    center = (image.shape[1] / 2, image.shape[0] / 2)

    # Makes a dictionary of bounding boxes using the bounding box as the key and its distance from the center as the value
    bboxes = {tuple(bbox): distance(center, (bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2)) for bbox in bboxes}

    # Finds the centermost bounding box
    bbox = min(bboxes, key=bboxes.get)

    # Attempts to start the tracker
    ok = tracker.init(image, bbox)
    print(ok)
    # Checks if the initialization was successful
    if ok:
        # Goes through each frame that occurred since the first image was found
        for frame in video:
            ok = draw(frame)

    # Returns the tracker's status
    return ok


# Updates the location of the object
def update(image):
    # Attempts to update the object's location
    ok, location = tracker.update(image)

    # Returns the location if the location was updated
    if ok:
        # Return centerpoint location (x, y)
        return (location[0] + location[2] / 2, location[1] + location[3] / 2)

    # Returns false the updating the location fails
    else:
        return False

def draw(image):
    print("in update")
    # Attempts to update the object's location
    ok, location = tracker.update(image)
    print(ok,location)
    # Returns the location if the location was updated
    if ok:
        image = Image(image).add_bounding_box(bounding_box=location).img
    else:
        tracker.clear()

    # Returns the updated image if successful, else just the image
    return image, ok
