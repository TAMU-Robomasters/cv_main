import cv2
# local imports
from toolbox.file_system_tools import FS

class Video(object):
    def __init__(self, path=None):
        self.path = path
        self._cached_video_capture = None # not always used
        
        # a helper method
        def _cv_get(value):
            if self._cached_video_capture is None:
                video_capture = cv2.VideoCapture(self.path)
            else:
                video_capture = self._cached_video_capture
            # Check if video opened successfully
            if (video_capture.isOpened()== False): 
                raise Exception(f"Error, tried opening {self.path} with cv2 but wasn't able to")
            
            output = video_capture.get(value)
            
            # if cached, then dont release cause something else is using it
            if self._cached_video_capture is None:
                video_capture.release()
            return output
        self._cv_get = _cv_get
            
    def frames(self):
        """
        returns: a generator, where each element is a image as a numpyarray 
        """
        if not FS.is_file(self.path):
            raise Exception(f"Error, tried opening {self.path} but I don't think that is a file")
        
        # detect type
        *folders, file_name, file_extension = FS.path_pieces(self.path)
        # video_format = None
        # print('file_extension = ', file_extension)
        # if file_extension == ".avi":
        #     video_format = cv2.VideoWriter_fourcc(*'aaaa')
        # print('video_format = ', video_format)
        
        # Path to video file 
        self._cached_video_capture = cv2.VideoCapture(self.path)
        # Check if video opened successfully
        if (self._cached_video_capture.isOpened()== False): 
            raise Exception(f"Error, tried opening {self.path} with cv2 but wasn't able to")
        
        # checks whether frames were extracted 
        success = 1
        while True: 
            # function extract frames 
            success, image = self._cached_video_capture.read()
            if not success:
                self._cached_video_capture.release()
                return None
            yield image
    
    def duration_estimate(self):
        frame_count = self.frame_count()
        fps = self.fps()
        duration = frame_count / fps
        if duration > 0:
            return duration
        else:
            return None
    
    def frames_with_info(self):
        """
        Example:
            for each_frame, each_index, each_time in video.frames_with_info():
                print('time in seconds:', each_time)
        """
        # 
        # each frame
        # 
        for each_index, each_frame in enumerate(self.frames()):
            # handle frame
            if type(each_frame) != type(None):
                miliseconds = self._cv_get(cv2.CAP_PROP_POS_MSEC)
                time = miliseconds/1000
            else:
                time = None
            yield each_frame, each_index, time
    
    def frame_count(self):
        frame_count = int(self._cv_get(cv2.CAP_PROP_FRAME_COUNT))
        # cv fails dangerously
        if int(frame_count) < 0:
            # do it the inefficient manual way, cause 21st centry software development is trash
            frame_count = 0
            for each in self.frames():
                frame_count += 1
            return frame_count
        return frame_count
        
    def fps(self):
        return self._cv_get(cv2.CAP_PROP_FPS)

    def frame_width(self):
        return int(self._cv_get(cv2.CAP_PROP_FRAME_WIDTH))
    
    def frame_width(self):
        return int(self._cv_get(cv2.CAP_PROP_FRAME_HEIGHT))
        
    def save_with_labels(self, list_of_labels, to=None):
        # 
        # extract video data
        # 
        video_capture = cv2.VideoCapture(self.path)
        frame_width  = int(video_capture.get(3))
        frame_height = int(video_capture.get(4))
        # Find OpenCV version
        (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')
        fps = video_capture.get(cv2.CAP_PROP_FPS)
        video_capture.release()
        
        # 
        # create new video source
        # 
        frame_dimensions = (frame_width, frame_height)
        if to is None:
            *folders, name, ext = FS.path_pieces(self.path)
            output_file = FS.join(*folders, name+".labelled"+ext)
        else:
            output_file = to
        new_video = cv2.VideoWriter(output_file, cv2.VideoWriter_fourcc(*'mp4v'), fps, frame_dimensions)
        # Read until video is completed
        for each_frame, each_label in zip(self.frames(), list_of_labels):
            if each_frame is None:
                break
            # Write text to frame
            text = str(each_label)
            text_location = (100, 100)
            font = cv2.FONT_HERSHEY_SIMPLEX
            thickness = 1
            color = (255, 255, 255)
            new_video.write(cv2.putText(each_frame, text, text_location, font, thickness, color, 2, cv2.LINE_AA))
        
        # combine the resulting frames into a video
        new_video.release()
    
    def save_clip(self, start, end, save_to):
        # todo: delete existing file in save_to
        # todo: validate start and end
        list_of_frames = []
        fps = self.fps()
        for each_frame, each_index, each_time in self.frames_with_time():
            if each_time >= start and each_time <= end:
                list_of_frames.append(each_frame)
        return Video.create_from_frames(list_of_frames, save_to=save_to, fps=fps)

    @classmethod
    def create_from_frames(self, list_of_frames, save_to=None, fps=30):
        # TODO: make this work with a generator
        # check
        if len(list_of_frames) == 0:
            raise Exception('The Video.create_from_frames was given an empty list (no frames)\nso a video cannot be made')
        elif save_to == None:
            raise Exception('The Video.create_from_frames was given no save_to= location so it doesn\'t know where to save the file')
        
        # 
        # create new video source
        # 
        frame_height, frame_width = list_of_frames[0].shape[:2]
        frame_dimensions = (frame_width, frame_height)
        new_video = cv2.VideoWriter(save_to, cv2.VideoWriter_fourcc(*'mp4v'), fps, frame_dimensions)
        # add all the frames
        for each_frame in list_of_frames:
            new_video.write(each_frame)    
        
        # combine the resulting frames into a video, which will write to a file
        new_video.release()