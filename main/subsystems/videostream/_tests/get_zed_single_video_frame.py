
#initializing stuff
import pyzed.sl as sl
import cv2

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
    print("ZED has image to grab.")
    zed.retrieve_image(image, sl.VIEW.LEFT)
    zed.retrieve_measure(depth_map, sl.MEASURE.DEPTH)

    # display image on desktop for debugging:
    # Use get_data() to get the numpy array
    image_ocv = image.get_data()
    # Display the left image from the numpy array
    cv2.imshow("Image", image_ocv)
    cv2.waitKey(5000)
    #accessing depth values
    print(depth_map.get_value(100,100))

    #displaying the depth image
    # you have to do this because it needs to change from 32-bit depth map to 
    # a 8 bit greyscale depth image
    depth_for_display = sl.Mat()
    zed.retrieve_image(depth_for_display, sl.VIEW.DEPTH)
else:
    print("ZED cannot grab image. Check connection.")
