import cv2
import time
import numpy as np
# import local
from toolbox.globals import path_to, config, print
from toolbox.image_tools import Image
from toolbox.video_tools import Video
from main import setup

# 
# import simulated inputs/outputs
# 

# simulated video
from subsystems.videostream.simulation import VideoStream
# simulated embedded output
from subsystems.embedded_communication._tests.simulated_output import send_output as simulated_send_output
# simulated modeling
import subsystems.modeling.modeling_main as test_modeling
# simulated tracking
import subsystems.tracking.tracking_main as test_tracking

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
    
    if config.testing.save_frame_to_file:
        frames.append(image.img)

    # allow user to quit by pressing q (at least I think thats what this checks)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        exit(0)

# 
# setup main(s)
# 
simple_synchronous, synchronous_with_tracker = setup(
    # comment out lines (arguments) below to get closer
    # and closer to realistic output
    on_next_frame=debug_each_frame,
    video_stream=VideoStream(),
    modeling=test_modeling,
    tracker=test_tracking,
    live_camera=False,
    kalman_filters=False,
    with_gui=config.testing.open_each_frame,
    filter_team_color=config.testing.filter_team_color,
    # send_output=simulated_send_output, # this should be commented in once we actually add aiming 
)

# 
# run mains (with simulated values)
# 
exec(config.testing.main_function+"()") # runs simple_synchronous

# save all the frames as a video
print("\nStarting process of saving frames to a video file")
Video.create_from_frames(frames, save_to=path_to.video_output)
print(f"video output has been saved to {path_to.video_output}")