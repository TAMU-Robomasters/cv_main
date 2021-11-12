import multiprocessing
import cv2
import time
import numpy as np
# import local
from toolbox.globals import MACHINE, PATHS, PARAMETERS, print
from toolbox.image_tools import Image
from toolbox.video_tools import Video
from main import setup

# 
# import simulated inputs/outputs
# 

# simulated video
import subsystems.videostream._tests.get_next_video_frame as next_video_frame
import subsystems.videostream._tests.get_latest_video_frame as latest_video_frame
# simulated embedded output
from subsystems.embedded_communication._tests.simulated_output import send_output as simulated_send_output
# simulated modeling
import subsystems.modeling._tests.test_modeling as test_modeling
# simulated tracking
import subsystems.tracking._tests.test_tracking as test_tracking
# simulated aiming 
import subsystems.aiming.filter as test_aiming

#
# debugger option #1
#
frames = []
def debug_each_frame(frame_index, frame, model_ouput, aiming_output):
    """
    this function is designed to be called every time main() processes a frame
    its only purpose is to bundle all of the debugging output
    """
        
    # extract the output
    boxes, confidences = model_ouput
    h_angle, v_angle = aiming_output
    
    # Display angle between center and bounding box in radians
    # if h_angle is not None and v_angle is not None:
    #     from toolbox.image_tools import add_text
    #     add_text(text="ANGLE: "+str(np.round(h_angle,2))+" "+str(np.round(v_angle,2)), location=(10,500), image=frame)

    # load/show the image
    image = Image(frame)
        
    for each in boxes:
        image.add_bounding_box(each)
    
    if PARAMETERS["testing"]["save_frame_to_file"]:
        frames.append(image.img)

    # allow user to quit by pressing q (at least I think thats what this checks)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        exit(0)

# decide method of sending frames
status =  PARAMETERS['videostream']['testing']['grab_frame']# 0 means grab next frame, 1 means grab latest frame, 2 means camera feed
path = PATHS["main_test_video"]
get_frame = None
if status == 0:
    get_frame = next_video_frame.NextFromVideo(path)
elif status == 1:
    get_frame = latest_video_frame.LatestFromVideo(path)

# 
# setup main(s)
# 
simple_synchronous, synchronous_with_tracker = setup(
    team_color=PARAMETERS["embedded_communication"]["team_color"],
    # comment out lines (arguments) below to get closer
    # and closer to realistic output
    get_frame = get_frame.get_frame, 
    on_next_frame=debug_each_frame,
    modeling=test_modeling,
    tracker=test_tracking,
    aiming=test_aiming,
    live_camera = False,
    kalman_filters = False,
    with_gui = PARAMETERS["testing"]["open_each_frame"],
    filter_team_color = PARAMETERS['testing']['filter_team_color']
    # send_output=simulated_send_output, # this should be commented in once we actually add aiming 
)

# 
# run mains (with simulated values)
# 

main_function = PARAMETERS['testing']['main_function']
print("MAIN",main_function)
if main_function == 0:
    simple_synchronous()
else:
    synchronous_with_tracker()

# save all the frames as a video
print.collect_prints = False
print() # dump any pending prints
print("\nStarting process of saving frames to a video file")
Video.create_from_frames(frames, save_to=PATHS["video_output"])
print(f"video output has been saved to {PATHS['video_output']}")