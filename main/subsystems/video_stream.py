from toolbox.globals import path_to, config, print

# this file just picks which one we need
if config.hardware.camera == 'zed':
    from subsystems.video_streaming.zed import VideoStream
elif config.hardware.camera == 'realsense':
    from subsystems.video_streaming.realsense import VideoStream
else:
    from subsystems.video_streaming.simulation import VideoStream
    
frames = VideoStream().frames