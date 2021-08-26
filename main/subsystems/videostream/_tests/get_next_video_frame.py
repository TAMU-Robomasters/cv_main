import time
# relative imports
from toolbox.video_tools import Video
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print

# 
# initilize
# 
class NextFromVideo:
    def __init__(self,path):
        test_video = Video(path)
        self.frame_generator = test_video.frames()
    def get_frame(self):
        try:
            return self.frame_generator.__next__()
        except StopIteration:
            None