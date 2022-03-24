import time
import itertools
import numpy as np
# relative imports
from toolbox.video_tools import Video
from toolbox.globals import path_to, config, print

simulation = config.videostream.simulation

class VideoStream:
    def __init__(self):
        self.video_object = Video(path=simulation.input_file)
        
        if simulation.grab_method == 'next_frame':
            pass # no special setup but demo the case for consistency and the error message
        elif simulation.grab_method == 'latest_frame':
            print('Loading all frames into ram for simulated testing')
            self.all_frames = tuple(self.video_object.frames())
            print(f'Found {len(all_frames)} frames')
            self.start_time = None
            self.framerate = simulated_output
            self.used_frames = set([])
        else:
            raise Exception(f'simulated VideoStream was created, but config.videostream.simulation.grab_frame was {simulation.grab_frame} instead of one of ["next_frame", "latest_frame"]')
    
    def frames(self):
        # for now it simply doesn't exist
        depth_frame = None
        
        # just pass along the frames
        if simulation.grab_method == 'next_frame':
            for color_frame in self.video_object.frames():
                yield color_frame, depth_frame
        elif simulation.grab_method == 'next_frame':
            self.start_time = time.time()
            for timestep in itertools.count(0): # starting at 0
                # figure out which frame should be retrieved based on the elapsed time
                seconds_since_start = time.time() - self.start_time 
                which_frame_index = int(seconds_since_start * self.framerate)
                # stop if too much time has passed
                if which_frame_index >= len(self.all_frames):
                    break
                
                yield self.all_frames[which_frame_index], depth_frame
        
    def save_video_if_needed(self):
        pass
