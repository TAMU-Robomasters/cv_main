from subprocess import call
import cv2
# local imports
from toolbox.file_system_tools import FS

# TODO: import this from globals
ENVIORMENT = "developer" 

# safety check, only runs in testing/developer mode
if ENVIORMENT == "developer":
    import distutils.spawn
    if distutils.spawn.find_executable("ffmpeg") is None:
        from os.path import basename
        raise Exception(f'Hey, the Video class {basename(__file__)} needs ffmpeg to be installed\nand it appears you don\'t have it installed')

class Video(object):
    def __init__(self, path=None):
        self.path = path
    
    # requires that ffmpeg be installed
    def get_frame(self, seconds, path):
        quality = "2" # can be 1-31, lower is higher quality
        call(["ffmpeg", "-ss", seconds, '-i', self.path , "-vframes", "1", "-q:v", quality, path])
    
    def frames(self):
        """
        returns: a generator, where each element is a image as a numpyarray 
        """
        # Path to video file 
        video_capture = cv2.VideoCapture(self.path)
        # Check if video opened successfully
        if (video_capture.isOpened()== False): 
            raise Exception(f"Error, tried opening {self.path} with cv2 but wasn't able to")
        
        # checks whether frames were extracted 
        success = 1
        while True: 
            # function extract frames 
            success, image = video_capture.read()
            if not success:
                video_capture.release()
                return None
            yield image
        
    
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
