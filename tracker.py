# Imports the MOSSE tracker from OpenCV
from cv2 import TrackerMOSSE_create

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

    # Finds the coordinate for the center of the screen
    center = (image.shape[1] / 2, image.shape[0] / 2)

    # Makes a dictionary of bounding boxes using the bounding box as the key and its distance from the center as the value
    bboxes = {bbox: distance(center, (bbox[0] + bbox[2] / 2, bbox[1] + bbox[3] / 2)) for bbox in bboxes}

    # Finds the centermost bounding box
    bbox = min(bboxes, key=bboxes.get)

    # Attempts to start the tracker
    ok = tracker.init(image, bbox)

    # Checks if the initialization was successful
    if ok:

        # Goes through each frame that occurred since the first image was found
        for frame in video:
            ok = update(frame)

    # Returns the tracker's status
    return ok
'''
def init(frame, bboxes):
    frame = cv2.imread(frame)
    # Finds the coordinate for the center of the screen
    center = (frame.shape[1] / 2, frame.shape[0] / 2)

    # Makes a dictionary of bounding boxes using the bounding box as the key and its distance from the center as the value
    for i in bboxes:
        x, y, width, height = i

        center_bbox = x + width / 2, y + height / 2

        cv2.imshow("Tracking", frame)


    #bboxes_dict = {bbox: distance(center, (center_bbox)) for bbox in bboxes}

    bboxes_dict = {}

    for i in bboxes:
        i = tuple(i)
        bboxes_dict = {i: distance(center, (center_bbox))}

    # Finds the centermost bounding box
    bbox = (0, 0, 0, 0)
    minimum = 999999
    for i in bboxes_dict:
        if bboxes_dict[i] < minimum:
            minimum = bboxes_dict[i]
            bbox = i
    print(minimum)
    print(bbox)



    p1 = (int(bbox[0]), int(bbox[1]))
    p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
    cv2.rectangle(frame, p1, p2, (255,0,0), 2, 1)

    cv2.imshow("Tracking", frame)
'''



# Updates the location of the object
def update(image):

    # Attempts to update the object's location
    ok, location = tracker.update(image)

    # Returns the location if the location was updated
    if ok:
        # return location
        return (location[0] + location[2] / 2, location[1] + location[3] / 2)

    # Returns false the updating the location fails
    else:
        return False
