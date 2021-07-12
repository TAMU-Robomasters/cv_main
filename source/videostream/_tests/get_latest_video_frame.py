import time
# relative imports
from toolbox.video_tools import Video
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print

class latestFromVideo:
    def __init__(self,path):
        test_video = Video(path)
        print('Loading all frames into ram for simulated testing')
        self.all_frames = list(test_video.frames())
        print(f'Found {len(all_frames)} frames')
        self.start_time = None
        self.framerate = PARAMETERS["videostream"]["testing"]["assumed_framerate"]
        self.usedFrames = set([])

    def getFrame(self):
        # kick of the start time if hasn't started yet
        if self.start_time == None:
            self.start_time = time.time()
        
        # figure out which frame should be retrieved based on the elapsed time
        seconds_since_start = time.time() - self.start_time 
        which_frame = int(seconds_since_start * self.framerate)
        
        
        # get that frame from the list of all frames
        if which_frame < len(self.all_frames):
            if which_frame not in self.usedFrames: # make sure we haven't used the frame already
                self.usedFrames.add(which_frame)
                return self.all_frames[which_frame]
            else:
                return 0 # indicate there are still frames to come
        else:
            return None # indicate the frames are over

# 
# smoketest for the simulated videostream
# 
if __name__ == '__main__':
    print('ENVIRONMENT = ', ENVIRONMENT)
    video = latestFromVideo()
    first_frame = video.get_latest_video_frame()
    seconds_of_wait_time = 2
    time.sleep(seconds_of_wait_time)
    later_frame = video.get_latest_video_frame()
    if first_frame is later_frame:
        print(f"\n\nin the simulated videostream, the first frame is equal to the frame {seconds_of_wait_time} seconds later\nthis is probably an error unless the video is 100% black for the first {seconds_of_wait_time} seconds")
        exit(1)
    elif first_frame is None or later_frame is None:
        print(f"\n\nin the simulated videostream, within the first {seconds_of_wait_time} seconds\none of the frames is equal to None, and it probably shouldn't be (it should be an image/array)")
        exit(1)
