import cv2
import time
from filter import Filter

tracker = cv2.TrackerMedianFlow_create()
video = cv2.VideoCapture("test.mp4")
ok, frame = video.read()
print(ok)
bbox = cv2.selectROI(frame, False)
ok = tracker.init(frame, bbox)
last_predicted_pt=None
t = 0.1
filter = Filter(t)

while True:
    # Read a new frame
    ok, frame = video.read()
    if not ok:
        break

    # Start timer
    timer = cv2.getTickCount()

    # Update tracker
    ok, bbox = tracker.update(frame)
    if last_predicted_pt is not None and \
        (last_predicted_pt[0]>bbox[0]+bbox[2] or last_predicted_pt[0]<bbox[0] or\
        last_predicted_pt[1]>bbox[1]+bbox[3] or last_predicted_pt[1]<bbox[1]):
        # Predicted point not in the bbox
        cv2.putText(frame, "Predicted point not in the bbox", (100, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)


    #TODO: Kalman filter predicts next position
    new_x = filter.predict(bbox)
    predicted_point=(int(new_x[0]), int(new_x[2]))
    #predicted_point=(300,300)
    last_predicted_pt=predicted_point

    fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer)
    # Draw predicted position
    cv2.circle(frame, predicted_point, 4, (0,0,255), 3)
    # Draw bounding box
    if ok:
        # Tracking success
        p1 = (int(bbox[0]), int(bbox[1]))
        p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
        cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
    else:
        # Tracking failure
        cv2.putText(frame, "Tracking failure detected", (100, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2)

    cv2.putText(frame, "FPS : " + str(int(fps)), (100, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (50, 170, 50), 2)
    cv2.imshow("Tracking", frame)

    # Slow down to visualize
    time.sleep(t)

    # Exit if ESC pressed
    k = cv2.waitKey(1) & 0xff
    if k == 27: break