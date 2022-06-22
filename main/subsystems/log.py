from time import time as now

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
runtime.prev_loop_time = 0 # init time value
def when_finished_processing_frame():
    display_information()
    record_images_if_needed()

def when_iteration_stops():
    save_frames_as_video(
        path=path_to.video_output,
    )

# 
# disable log check
# 
if config.testing.disable_logging:
    # override above definition and disable
    def when_finished_processing_frame():
        pass # do nothing intentionally

# 
# 
# helpers
# 
# 
def display_information():  
    frame_number       = runtime.frame_number
    color_image        = runtime.color_image
    depth_image        = runtime.depth_image
    prev_loop_time     = runtime.prev_loop_time
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
    now_in_miliseconds = now() * 1000
    iteration_time = now_in_miliseconds-prev_loop_time
    runtime.prev_loop_time = now_in_miliseconds
    
    # relase all print info on one line
    print(f'\nframe#:{f"{frame_number}".rjust(5)},{f"{iteration_time}".rjust(4)}ms,', sep='', end='', flush=True)

    # Show live feed is gui is enabled
    if with_gui:
        from toolbox.image_tools import add_text
        add_text(text="horizontal_angle: "+str(round(horizontal_angle,2)     ), location=(30, 50), image=color_image)
        add_text(text="vertical_angle: "  +str(round(vertical_angle,2)       ), location=(30,100), image=color_image)
        add_text(text="depth_amount: "    +str(round(depth_amount,2)         ), location=(30,150), image=color_image)
        add_text(text="pixel_diff: "      +str(round(pixel_diff,2)           ), location=(30,200), image=color_image)
        add_text(text="x_std: "           +str(round(x_std,2)                ), location=(30,250), image=color_image)
        add_text(text="y_std: "           +str(round(y_std,2)                ), location=(30,300), image=color_image)
        add_text(text="confidence: "      +str(round(current_confidence,2)   ), location=(30,350), image=color_image)
        add_text(text="fps: "             +str(round(1000/iteration_time,2)  ), location=(30,400), image=color_image)
        add_text(text="shoot: "           +str(should_shoot                  ), location=(30,450), image=color_image)

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

def visualize_depth_frame(depth_frame_array):
    """
    Displays a depth frame in a visualized color format.

    Input: Depth Frame.
    Output: None.
    """
    import cv2
    depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_frame_array, alpha = 0.04), cv2.COLORMAP_JET)# this puts a color efffect on the depth frame
    images = depth_colormap                              # use this for individual streams
    cv2.namedWindow('Align Example', cv2.WINDOW_NORMAL)   # names and shows the streams
    cv2.imwrite('depthmap.jpg', images)

    # # if you press escape or q you can cancel the process
    key = cv2.waitKey(1)
    print("press escape to cancel")
    if key & 0xFF == ord('q') or key == 27:
        cv2.destroyAllWindows()