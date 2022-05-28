import time
import numpy as np

# relative imports
from toolbox.video_tools import Video
from toolbox.globals import path_to, config, print

videostream = config.videostream
aiming      = config.aiming

class VideoStream:
    def __init__(self):
        import pyrealsense2 as rs
        
        stream_width  = aiming.stream_width
        stream_height = aiming.stream_height
        framerate     = aiming.stream_framerate
        
        self.video_output = None
        if videostream.testing.record_interval > 0:
            self.video_output = self.begin_video_recording()

        self.pipeline = rs.pipeline()                                                               # declares and initializes the pipeline variable
        rs_config = rs.config()                                                                        # declares and initializes the config variable for the pipeline
        rs_config.enable_stream(rs.stream.depth, stream_width, stream_height, rs.format.z16, framerate)  # this starts the depth stream and sets the size and format
        rs_config.enable_stream(rs.stream.color, stream_width, stream_height, rs.format.bgr8, framerate) # this starts the color stream and set the size and format
        # config.enable_stream(rs.stream.accel,rs.format.motion_xyz32f,250)
        # config.enable_stream(rs.stream.gyro,rs.format.motion_xyz32f,200)
        # config.enable_stream(rs.stream.pose,rs.format.motion_xyz32f,200)
        self.que = rs.queue(1)
        while True:
            try:
                self.pipeline.start(rs_config, que)
            except Exception as error:
                print("")
                print(error)
                print("trying again")
                continue
            # exit loop if successful
            break
    
    def frames(self):
        frame_number = 0
        # retry after failure
        while True:
            try:
                frame = self.que.wait_for_frame().as_frame()
                frame_number += 1
                # create the frames
                color_frame = np.array(frame.get_color_frame().get_data()) 
                depth_frame = np.array(frame.get_depth_frame() .get_data()) 
                
                # Add frame to video recording based on recording frequency
                if self.video_output and (frame_number % videostream.testing.record_interval == 0):
                    print(" saving_frame:",frame_number)
                    self.video_output.write(color_frame)
                    
                yield color_frame, depth_frame
                
            except Exception as error:
                import sys
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