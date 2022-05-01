from toolbox.globals import path_to, config, print

# this file just picks which one we need
if config.hardware.camera == 'zed':
    from subsystems.video_stream.zed import VideoStream
elif config.hardware.camera == 'realsense':
    from subsystems.video_stream.realsense import VideoStream
else:
    from subsystems.video_stream.simulation import VideoStream
    
# create/export the video stream object
video_stream = VideoStream()