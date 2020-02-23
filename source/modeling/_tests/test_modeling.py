import cv2
from PIL import Image
from datetime import datetime
# relative imports
from toolbox.globals import PATHS, ENVIRONMENT, MODE, MODEL_COLORS, MODEL_LABELS
from source.modeling.modeling_main import get_bounding_boxes as original_get_bounding_boxes

def get_bounding_boxes(frame, iconfidence, ithreshold):
    """
    this function is the debugging counterpart to the actual get_bounding_boxes()
    
    @frame: should be an cv2 image (basically a numpy array)
    @iconfidence: should be a value between 0-1
    @ithreshold: should be a value between 0-1
    
    returns:
        a list of bounding boxes, each formatted as (x,y, width, height)
    
    """
    
    # 
    # wrap the original, but display every frame
    # 
    boxes, confidences, class_ids = original_get_bounding_boxes(frame, iconfidence, ithreshold)
    if MODE == "production":
        return boxes, confidences, class_ids
    
    # apply non-maxima suppression to suppress weak, overlapping
    # bounding boxes
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, iconfidence, ithreshold)
    
    # ensure at least one detection exists
    if len(idxs) > 0:
        # loop over the indexes we are keeping
        for i in idxs.flatten():
            # extract the bounding box coordinates

            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])
            # draw a bounding box rectangle and label on the frame
            color = [int(c) for c in MODEL_COLORS[class_ids[i]]]
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            text = "{}: {:.4f}".format(MODEL_LABELS[class_ids[i]],confidences[i])
            cv2.putText(frame, text, (x, y - 5),cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    current_time = datetime.now().strftime("%H:%M:%S")
    print(current_time)
    img = Image.fromarray(frame, 'RGB')
    img.save(PATHS['frame_save_location'])
    img.show() if ENVIRONMENT != "docker" else None
    print("bounding boxes from model:", boxes)
    
    return boxes, confidences, class_ids


if __name__ == '__main__':
    # FIXME: create the actual test for modeling
    pass