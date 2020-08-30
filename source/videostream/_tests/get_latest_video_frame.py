import time
# relative imports
from toolbox.video_tools import Video
from toolbox.globals import PATHS, PARAMETERS, ENVIRONMENT

# 
# initilize
# 
test_video = Video(PATHS["main_test_video"])
print('Loading all frames into ram for simulated testing')
all_frames = list(test_video.frames())
start_time = None
framerate = PARAMETERS["videostream"]["testing"]["assumed_framerate"]

def get_latest_video_frame():
    # kick of the start time if hasn't started yet
    global start_time
    if start_time == None:
        start_time = time.time()
    
    # figure out which frame should be retrieved based on the elapsed time
    seconds_since_start = time.time() - start_time 
    which_frame = int(seconds_since_start * framerate)
    
    # get that frame from the list of all frames
    if which_frame < len(all_frames):
        return all_frames[which_frame]
    else:
        return None

# 
# smoketest for the simulated videostream
# 
if __name__ == '__main__':
    print('ENVIRONMENT = ', ENVIRONMENT)
    first_frame = get_latest_video_frame()
    seconds_of_wait_time = 2
    time.sleep(seconds_of_wait_time)
    later_frame = get_latest_video_frame()
    if first_frame is later_frame:
        print(f"\n\nin the simulated videostream, the first frame is equal to the frame {seconds_of_wait_time} seconds later\nthis is probably an error unless the video is 100% black for the first {seconds_of_wait_time} seconds")
        exit(1)
    elif first_frame is None or later_frame is None:
        print(f"\n\nin the simulated videostream, within the first {seconds_of_wait_time} seconds\none of the frames is equal to None, and it probably shouldn't be (it should be an image/array)")
        exit(1)
