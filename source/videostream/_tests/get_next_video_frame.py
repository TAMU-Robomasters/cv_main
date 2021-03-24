import time
# relative imports
from toolbox.video_tools import Video
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print

# 
# initilize
# 
class nextFromVideo:
    def __init__(self,path):
        test_video = Video(path)
        self.frame_generator = test_video.frames()
    def getFrame(self):
        try:
            return self.frame_generator.__next__()
        except StopIteration:
            None