import time
# relative imports
from toolbox.video_tools import Video
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print

# 
# initilize
# 
streamWidth = PARAMETERS['aiming']['stream_width']
streamHeight = PARAMETERS['aiming']['stream_height']
framerate = PARAMETERS['aiming']['stream_framerate']
gridSize = PARAMETERS['aiming']['grid_size']

pipeline = rs.pipeline()                                            # declares and initializes the pipeline variable
config = rs.config()                                                # declares and initializes the config variable for the pipeline
config.enable_stream(rs.stream.depth, streamWidth, streamHeight, rs.format.z16, framerate)  # this starts the depth stream and sets the size and format
config.enable_stream(rs.stream.color, streamWidth, streamHeight, rs.format.bgr8, framerate) # this starts the color stream and set the size and format
profile = pipeline.start(config)
counter = 0
def get_live_video_frame():
    counter+=1
    if counter == 500
        return None
    try:
        frames = pipeline.wait_for_frames()     
        color_frame = frames.get_color_frame()  
        if not color_frame:
            return 0
        # we turn the depth and color frames into numpy arrays because we need to draw a rectangle and stack the two arrays
        color_image = np.asanyarray(color_frame.get_data()) 
        # causes 1FPS Drop
        return color_image
    except:
        return None