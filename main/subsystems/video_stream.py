from toolbox.globals import path_to, config, print

# 
# select which file to import from
# 
if config.hardware.camera == 'zed':
    from subsystems.video_streaming.zed import VideoStream
elif config.hardware.camera == 'realsense':
    from subsystems.video_streaming.realsense import VideoStream
else:
    from subsystems.video_streaming.simulation import VideoStream
    
# simplify the export
frames_function = VideoStream().frames

# 
# flip if needed
# 
if not config.hardware.camera_is_upsidedown:
    frames = frames_function
else:
    def frames():
        for frame_number, color_image, depth_image in frames_function():
            yield (
                frame_number,
                Image(color_image).rotated_180_degrees().in_cv2_format,
                Image(depth_image).rotated_180_degrees().in_cv2_format,
            )
