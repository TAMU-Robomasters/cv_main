import numpy as np
import cv2
# relative imports
from toolbox.globals import PATHS, MODE


# TODO: I don't know what this number is, and we should probably figure it out
MAGIC_NUMBER_1 = 416

# 
# init the model
# 
print("[INFO] loading YOLO from disk...") if MODE == "development" else None
net = cv2.dnn.readNetFromDarknet(PATHS["model_config"], PATHS["model_weights"])
layer_names = net.getLayerNames()
output_layer_names = [ layer_names[index[0] - 1] for index in net.getUnconnectedOutLayers() ]
W, H = None, None

def get_bounding_boxes(frame, iconfidence, ithreshold):
    """
    ex: boxes, confidences, class_ids = get_bounding_boxes(frame, 0.5, 0.3)
    
    @frame: should be an cv2 image (basically a numpy array)
    @iconfidence: should be a value between 0-1
    @ithreshold: should be a value between 0-1
    -
    @@returns:
    - a tuple containing
        - a list of bounding boxes, each formatted as (x, y, width, height)
        - a list of confidences
        - a list of class_ids
    NOTE: this code is derived from https://www.pyimagesearch.com/2018/11/12/yolo-object-detection-with-opencv/
    """
    
    global W,H
    # if the frame dimensions are empty, grab them
    if W is None or H is None:
        (H, W) = frame.shape[:2]

    # convert image to blob before running it in the model
    blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (MAGIC_NUMBER_1, MAGIC_NUMBER_1), swapRB=True, crop=False)
    # provide input and retrive output
    net.setInput(blob)
    layerOutputs = net.forward(output_layer_names)

    # initialize our lists of detected bounding boxes, confidences,
    # and class IDs, respectively
    boxes = []
    confidences = []
    classIDs = []

    # loop over each of the layer outputs
    for output in layerOutputs:
        # loop over each of the detections
        for detection in output:
            # extract the class ID and confidence (i.e., probability)
            # of the current object detection
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]

            # filter out weak predictions by ensuring the detected
            # probability is greater than the minimum probability
            if confidence > iconfidence:
                # scale the bounding box coordinates back relative to
                # the size of the image, keeping in mind that YOLO
                # actually returns the center (x, y)-coordinates of
                # the bounding box followed by the boxes' width and
                # height
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")

                # use the center (x, y)-coordinates to derive the top
                # and and left corner of the bounding box
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                # update our list of bounding box coordinates,
                # confidences, and class IDs
                boxes.append([x, y, int(width), int(height)])

                confidences.append(float(confidence))
                classIDs.append(classID)

    return boxes, confidences, classIDs