import time
# relative imports
from toolbox.video_tools import Video
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print

# 
# initilize
# 
test_video = Video(PATHS["main_test_video"])
frame_generator = test_video.frames()

def get_next_video_frame():
    try:
        return frame_generator.__next__()
    except StopIteration:
        None