from subprocess import call
import cv2
import skvideo.io
# local imports
from toolbox.file_system_tools import FS


# FIXME: rewrite this tool so that it doens't use cv2

class Video(object):
    def __init__(self, path=None):
        self.path = path
    
    
    def frames(self):
        """
        returns: a generator, where each element is a image as a numpyarray 
        """
        # Path to video file 
        return skvideo.io.vreader(self.path)
    
    def fps(self):
        video_capture = cv2.VideoCapture(self.path)
        # Find OpenCV version
        (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')
        if int(major_ver) < 3:
            fps = video_capture.get(cv2.cv.CV_CAP_PROP_FPS)
        else:
            fps = video_capture.get(cv2.CAP_PROP_FPS)
        video_capture.release()
        return fps

    def frame_width(self):
        video_capture = cv2.VideoCapture(self.path)
        frame_width  = int(video_capture.get(3))
        video_capture.release()
        return frame_width
    
    def frame_height(self):
        video_capture = cv2.VideoCapture(self.path)
        frame_height = int(video_capture.get(4))
        video_capture.release()
        return frame_height
    
    def save_with_labels(self, list_of_labels, to=None):
        # 
        # extract video data
        # 
        video_capture = cv2.VideoCapture(self.path)
        frame_width  = int(video_capture.get(3))
        frame_height = int(video_capture.get(4))
        # Find OpenCV version
        (major_ver, minor_ver, subminor_ver) = (cv2.__version__).split('.')
        if int(major_ver) < 3:
            fps = video_capture.get(cv2.cv.CV_CAP_PROP_FPS)
        else:
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

    @classmethod
    def create_from_frames(self, list_of_frames, save_to=None, fps=30):
        # check
        if len(list_of_frames) == 0:
            raise Exception('The Video.create_from_frames was given an empty list (no frames)\nso a video cannot be made')
        elif save_to == None:
            raise Exception('The Video.create_from_frames was given no save_to= location so it doesn\'t know where to save the file')
        
        skvideo.io.vwrite(save_to, list_of_frames)