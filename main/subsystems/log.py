import numpy as np
import time

from toolbox.globals import path_to, config, print, runtime
from toolbox.video_tools import Video
from toolbox.image_tools import Image

# 
# config
# 
with_gui = config.testing.display_live_frames


# 
# 
# main
# 
# 
def when_finished_processing_frame():
    display_information()
    record_images_if_needed()

def when_iteration_stops():
    save_frames_as_video(
        path=path_to.video_output,
    )

# 
# 
# helpers
# 
# 
def display_information():  
    frame_number       = runtime.frame_number
    color_image        = runtime.color_image
    depth_image        = runtime.depth_image
    initial_time       = runtime.initial_time
    found_robot        = runtime.modeling.found_robot
    current_confidence = runtime.modeling.current_confidence
    should_shoot       = runtime.aiming.should_shoot
    horizontal_angle   = runtime.aiming.horizontal_angle
    vertical_angle     = runtime.aiming.vertical_angle
    depth_amount       = runtime.aiming.depth_amount
    pixel_diff         = runtime.aiming.pixel_diff
    x_std              = runtime.aiming.x_std
    y_std              = runtime.aiming.y_std

    # If gui is enabled then draw bounding boxes around the selected robot
    if with_gui and found_robot:
        cv2.rectangle(found_robot, color_image, (best_bounding_box[0], best_bounding_box[1]), (best_bounding_box[0] + best_bounding_box[2], best_bounding_box[1] + best_bounding_box[3]), (255,0,0), 2)  

    # Display time taken for single iteration of loop
    iteration_time = time.time()-initial_time
    # relase all print info on one line
    print(f'\nframe#: {frame_number} model took: {iteration_time:.4f}sec,', sep='', end='', flush=True)

    # Show live feed is gui is enabled
    if with_gui:
        from toolbox.image_tools import add_text
        add_text(text="horizontal_angle: "+str(np.round(horizontal_angle,2)), location=(30, 50), image=color_image)
        add_text(text="vertical_angle: "  +str(np.round(vertical_angle,2))  , location=(30,100), image=color_image)
        add_text(text="depth_amount: "    +str(np.round(depth_amount,2))    , location=(30,150), image=color_image)
        add_text(text="pixel_diff: "      +str(np.round(pixel_diff,2))      , location=(30,200), image=color_image)
        add_text(text="x_std: "           +str(np.round(x_std,2))           , location=(30,250), image=color_image)
        add_text(text="y_std: "           +str(np.round(y_std,2))           , location=(30,300), image=color_image)
        add_text(text="confidence: "      +str(np.round(current_confidence,2))              , location=(30,350), image=color_image)
        add_text(text="fps: "             +str(np.round(1/iteration_time,2)), location=(30,400), image=color_image)
        add_text(text="shoot: "           +str(should_shoot)                , location=(30,450), image=color_image)

        cv2.imshow("RGB Feed",color_image)
        cv2.waitKey(10)


frames = []
def record_images_if_needed():
    """
    this function is designed to be called every time main() processes a frame
    its only purpose is to bundle all of the debugging output
    """
    
    if config.testing.save_frame_to_file:
        image = Image(runtime.color_image)
        for each in runtime.modeling.boxes:
            image.add_bounding_box(each)
        
        frames.append(image.img)

def save_frames_as_video(path):
    if config.testing.save_frame_to_file:
        # save all the frames as a video
        Video.create_from_frames(frames, save_to=path)
        print(f"\n\nvideo output has been saved to {path}")