import time
# relative imports
from toolbox.video_tools import Video
from toolbox.globals import PATHS, PARAMETERS, ENVIRONMENT

# 
# initilize
# 
test_video = Video(PATHS["main_test_video"])

def get_next_video_frame():
    for each_frame in test_video.frames():
        yield each_frame