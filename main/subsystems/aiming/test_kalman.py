import time
import numpy as np
import sys
import cv2
import subsystems.aiming.filter as f
import subsystems.aiming.depth_camera as dc

# project imports
from toolbox.globals import path_to, config, print

npy_frames_location = path_to.npy_frames
stream_width = config.aiming.stream_width
stream_height = config.aiming.stream_height
kalman_video_path = path_to.kalman_video
framerate = config.aiming.stream_framerate
grid_size = config.aiming.grid_size
model_fps = config.aiming.model_fps

counter = 0
colors = []
depths = []
bboxs = []
preds = []
preds_0_5 = []
preds_1 = []

try:
    while True: # keep getting frames until we run out
        counter+=1
        print("PROCESSING FRAME:",counter)
        color_frame = np.load(npy_frames_location+"/"+str(counter)+"color.do_not_sync.npy").reshape(stream_height,stream_width,3)
        depth_frame = np.load(npy_frames_location+"/"+str(counter)+"depth.do_not_sync.npy").reshape(stream_height,stream_width)/1000
        bbox = np.load(npy_frames_location+"/"+str(counter)+"bbox.do_not_sync.npy").flatten()

        colors.append(color_frame)
        depths.append(depth_frame)
        bboxs.append(bbox)
        
except Exception as e: # this will always run since we run out of frames
    print("FINISHED LOADING IMAGES")
    print("YOU CAN IGNORE THIS EXCEPTION IF YOUR DATA LOOKS GOOD (KEPT FOR DEBUGGING PURPOSES):", e)
finally:
    # DO WHATEVER YOU WANT WITH THE FRAMES HERE


    # filter = f.Filter(5)
    # dc.visualize_depth_frame(depths[220])
    depth_value = 1.0
    filter = f.Filter(model_fps)
    for i in range(len(depths)):

        bbox = bboxs[i]
        depth = depths[i]
        if ((bbox == [-1, -1, -1, -1]).all()):
            preds.append(np.array([-1, -1, -1, -1]))
            preds_0_5.append(np.array([-1, -1, -1, -1]))
            preds_1.append(np.array([-1, -1, -1, -1]))

            print()
            print("INVALID BBOX INVALID BBOX INVALID BBOX",i)
            continue
        
        # depth_value = dc.get_dist_from_array(depth, bbox, grid_size)
        
        X = filter.predict([bbox[0]+bbox[2]/2, bbox[1]+bbox[3]/2, depth_value])
        preds.append(np.array([X[0]-bbox[2]/2, X[1]-bbox[3]/2, bbox[2], bbox[3]]))
        print("0.033:",X)
        depth_value += 0.2
        # time = dc.travelTime(depth_value)
        # X0_5 = filter.time_predict(0.5)
        # preds_0_5.append(np.array([X0_5[0]-bbox[2]/2, X0_5[2]-bbox[3]/2, bbox[2], bbox[3]]))

        # # 1 second filter

        # X1 = filter.time_predict(1)
        # preds_1.append(np.array([X1[0]-bbox[2]/2, X1[2]-bbox[3]/2, bbox[2], bbox[3]]))


        
    




    # debug and video, the current video will be outputted named kalman video so you can see
    frame_dimensions = (stream_width, stream_height)
    colorwriter = cv2.VideoWriter(kalman_video_path, cv2.VideoWriter_fourcc(*'mp4v'), framerate, frame_dimensions)

    for loc in range(len(colors)):
        frame = colors[loc]
        bbox = preds[loc]
        # bbox_0_5 = preds_0_5[loc]
        # bbox_1 = preds_1[loc]

        x, y, w, h = bboxs[loc].astype(int)
        if ((bbox == [-1, -1, -1, -1]).all() == False):
            x1, y1, w1, h1 = bbox.astype(int)
            cv2.rectangle(frame, (x1, y1), (x1 + w1, y1 + h1), (255,0,0), 2)
        # if ((bbox_0_5 == [-1, -1, -1, -1]).all() == False):
        #     x1, y1, w1, h1 = bbox_0_5.astype(int)
        #     cv2.rectangle(frame, (x1, y1), (x1 + w1, y1 + h1), (0,255,0), 2)
        # if ((bbox_1 == [-1, -1, -1, -1]).all() == False):
        #     x1, y1, w1, h1 = bbox_1.astype(int)
        #     cv2.rectangle(frame, (x1, y1), (x1 + w1, y1 + h1), (0,0,255), 2)

        # draw a bounding box rectangle and label on the frame
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255,255,255), 2)
        colorwriter.write(frame)

    colorwriter.release()