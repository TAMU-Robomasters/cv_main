import cv2
# import local
from toolbox.globals import ENVIRONMENT, PATHS
from toolbox.image_tools import Image
from toolbox.video_tools import Video
from source.main import setup
# import simulated/debugging inputs rather than the real-deal
from source.videostream._tests.simulated_videostream import get_latest_frame as simulated_get_latest_frame
from source.embedded_communication._tests.simulated_output import send_output as simulated_send_output
import source.modeling._tests.test_modeling as test_modeling
import source.tracking._tests.test_tracking as test_tracking

#
# debugger option #1
#
frames = []
def debug_each_frame(counter, frame, model_ouput, aiming_output):
    """
    this function is designed to be called every time main() processes a frame
    its only purpose is to bundle all of the debugging output
    """
    
    # extract the output
    boxes, confidences = model_ouput
    x,y,z = aiming_output
    
    # load/show the image
    image = Image(frame)
    for each in boxes:
        image.add_bounding_box(each)
    if ENVIRONMENT == 'docker':
        frames.append(image.img)
    else:
        image.show("frame")

    # allow user to quit by pressing q (at least I think thats what this checks)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        exit(0)

# 
# setup main(s)
# 
simple_synchronous, synchronous_with_tracker = setup(
    # comment out lines (arguments) below to get closer
    # and closer to realistic output
    get_latest_frame=simulated_get_latest_frame,
    on_next_frame=debug_each_frame,
    modeling=test_modeling,
    tracker=test_tracking,
    send_output=simulated_send_output   
)

# 
# run mains (with simulated values)
# 
print('Starting simple_synchronous with simulated IO (rather than real IO)')
simple_synchronous()

# save all the frames as a video
Video.create_from_frames(frames, save_to=PATHS["video_output"])
print(f"video output has been saved to {PATHS['video_output']}")