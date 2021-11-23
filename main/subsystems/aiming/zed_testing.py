
#initializing stuff
import pyzed.sl as sl


zed = sl.Camera();

init_params = sl.InitParameters()
init_params.camera_resolution = sl.RESOLUTION.HD1080
init_params.camera_fps = 30
init_params.depth_mode = sl.DEPTH_MODE.ULTRA
init_params.coordinate_units = sl.UNIT.METER

err = zed.open(init_params)
if err != sl.ERROR_CODE.SUCCESS:
    exit(-1)

#getting the rgb and depth frames
image = sl.Mat()
depth_map = sl.Mat()
runtime_parameters = sl.RuntimeParameters()
if zed.grab(runtime_parameters) == sl.ERROR_CODE.SUCCESS:
    zed.retrieve_image(image, sl.VIEW.LEFT)
    zed.retreive_measure(depth_map, sl.MEASURE.DEPTH)

#accessing depth values
print(depth_map.get_value(100,100));

#displaying the depth image
# you have to do this because it needs to change from 32-bit depth map to 
# a 8 bit greyscale depth image
depth_for_display = sl.Mat()
zed.retreive_image(depth_for_display, sl.VIEW.DEPTH)
