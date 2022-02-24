import time
# relative imports
from toolbox.video_tools import Video
from toolbox.globals import path_to, config, print
from toolbox.globals import path_to, config, print
import numpy as np

videostream = config.videostream
aiming      = config.aiming

class VideoStream:
    def __init__(self):
        stream_width  = aiming.stream_width
        stream_height = aiming.stream_height
        framerate     = aiming.stream_framerate
        
        self.video_output = None
        if videostream.testing.record_interval > 0:
            self.video_output = self.begin_video_recording()

        self.pipeline = rs.pipeline()                                                               # declares and initializes the pipeline variable
        config = rs.config()                                                                        # declares and initializes the config variable for the pipeline
        config.enable_stream(rs.stream.depth, stream_width, stream_height, rs.format.z16, framerate)  # this starts the depth stream and sets the size and format
        config.enable_stream(rs.stream.color, stream_width, stream_height, rs.format.bgr8, framerate) # this starts the color stream and set the size and format
        # config.enable_stream(rs.stream.accel,rs.format.motion_xyz32f,250)
        # config.enable_stream(rs.stream.gyro,rs.format.motion_xyz32f,200)
        # config.enable_stream(rs.stream.pose,rs.format.motion_xyz32f,200)
        self.pipeline.start(config)
    
    def frames(self):
        frame_number = 0
        # retry after failure
        while True:
            try:
                frames = self.pipeline.wait_for_frames()
                for frame in frames:
                    frame_number += 1
                    # create the frames
                    color_frame = np.asanyarray(frame.get_color_frame().get_data()) 
                    depth_frame = np.asanyarray(frame.get_depth_frame() .get_data()) 
                    
                    # Add frame to video recording based on recording frequency
                    if self.video_output and (frame_number % videostream.testing.record_interval == 0):
                        print(" saving_frame:",frame_number)
                        self.video_output.write(color_frame)
                    
                    yield color_image, depth_image
                
            except Exception as error:
                print("VideoStream: error while getting frames:", error, sys.exc_info()[0])
                print('(retrying)')
        
    def __del__(self):
        print("Closing Realsense Pipeline")
        self.pipeline.stop()
    
    def begin_video_recording(self):
        """
        Run live video recording using nvenc.

        Input: None
        Output: Video object to add frames too.
        """

        color_video_location = path_to.record_video_output_color
        
        # Setup video output path based on date and counter
        c = 1
        file_path = color_video_location.replace(".do_not_sync",datetime.datetime.now().strftime("%Y-%m-%d")+"_"+str(c)+".do_not_sync")
        while os.path.isfile(file_path):
            c += 1
            file_path = color_video_location.replace(".do_not_sync",datetime.datetime.now().strftime("%Y-%m-%d")+"_"+str(c)+".do_not_sync")

        # Start up video output
        gst_out = "appsrc ! video/x-raw, format=BGR ! queue ! videoconvert ! video/x-raw,format=BGRx ! nvvidconv ! nvv4l2h264enc ! h264parse ! matroskamux ! filesink location="+file_path
        video_output = cv2.VideoWriter(gst_out, cv2.CAP_GSTREAMER, 0, float(framerate), (int(stream_width), int(stream_height)))
        if not video_output.isOpened():
            print("Failed to open output")

        return video_output    
    
    def save_video_if_needed(self):
        # Save video output
        if self.video_output:
            print("Saving Recorded Video")
            self.video_output.release()
            print("Finished Saving Video")