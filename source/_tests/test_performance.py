import multiprocessing
import cv2
import time
# import local
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print
from toolbox.image_tools import Image
from toolbox.video_tools import Video
from source.main import setup

# 
# import simulated inputs/outputs
# 

# simulated video
from source.videostream._tests.get_next_video_frame import get_next_video_frame
from source.videostream._tests.get_latest_video_frame import get_latest_video_frame
# simulated embedded output
from source.embedded_communication._tests.simulated_output import send_output as simulated_send_output
# simulated modeling
import source.modeling._tests.test_modeling as test_modeling
# simulated tracking
import source.tracking._tests.test_tracking as test_tracking
# simulated aiming 
import source.aiming._tests.test_aiming as test_aiming

#
# debugger option #1
#
frames = []
def debug_each_frame(frame_index, frame, model_ouput, aiming_output):
    """
    this function is designed to be called every time main() processes a frame
    its only purpose is to bundle all of the debugging output
    """
    
    print(f'processing frame {frame_index}')
    
    # extract the output
    boxes, confidences = model_ouput
    x, y = aiming_output
    
    # load/show the image
    image = Image(frame)
        
    for each in boxes:
        image.add_bounding_box(each)
    
    if PARAMETERS["testing"]["save_frame_to_file"]:
        frames.append(image.img)
    
    if PARAMETERS["testing"]["open_each_frame"]:
        # NOTE: this currently fails in nix-shell on Mac with error message:
        #     qt.qpa.plugin: Could not find the Qt platform plugin "cocoa" in ""
        #     its fixable, see "qt.qpa.plugin: Could not find the Qt" on https://nixos.wiki/wiki/Qt
        #     but its hard to fix
        image.show("frame")

    # allow user to quit by pressing q (at least I think thats what this checks)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        exit(0)

# 
# setup main(s)
# 
simple_synchronous, synchronous_with_tracker,multiprocessing_with_tracker = setup(
    # comment out lines (arguments) below to get closer
    # and closer to realistic output
    get_frame=get_next_video_frame if PARAMETERS['videostream']['testing']['grab_frame']==0 else get_latest_video_frame, # 0 means grab next frame, 1 means grab latest frame
    on_next_frame=debug_each_frame,
    modeling=test_modeling,
    tracker=test_tracking,
    aiming=test_aiming
    # send_output=simulated_send_output, # this should be commented in once we actually add aiming 
)

# 
# run mains (with simulated values)
# 
t0 = time.time()

main_function = PARAMETERS['testing']['main_function']
print("MAIN",main_function)
if main_function == 0:
    simple_synchronous()
elif main_function == 1:
    synchronous_with_tracker()
else:
    multiprocessing_with_tracker()

t1 = time.time()
with open(PATHS["time_output"],'w') as f:
    f.write("Time Taken: "+str(t1-t0)+" seconds")


# save all the frames as a video
print("Starting process of saving frames to a video file")
Video.create_from_frames(frames, save_to=PATHS["video_output"])
print(f"video output has been saved to {PATHS['video_output']}")