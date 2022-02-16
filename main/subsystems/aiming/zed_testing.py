
# #initializing stuff
# import cv2
# import pyzed.sl as sl


# zed = sl.Camera();

# init_params = sl.InitParameters()
# init_params.camera_resolution = sl.RESOLUTION.HD1080
# init_params.camera_fps = 30
# init_params.depth_mode = sl.DEPTH_MODE.ULTRA
# init_params.coordinate_units = sl.UNIT.METER

# err = zed.open(init_params)
# if err != sl.ERROR_CODE.SUCCESS:
#     exit(-1)

# #getting the rgb and depth frames
# image = sl.Mat()
# depth_map = sl.Mat()
# runtime_parameters = sl.RuntimeParameters()
# if zed.grab(runtime_parameters) == sl.ERROR_CODE.SUCCESS:
#     zed.retrieve_image(image, sl.VIEW.LEFT)
#     image_ocv = image.get_data()
#     zed.retrieve_measure(depth_map, sl.MEASURE.DEPTH) 
#     depth_ocv = depth_map.get_data()
#     cv2.imshow("image", image_ocv)

# # image_depth_zed = sl.Mat()

# # if zed.grab() == sl.ERROR_CODE.SUCCESS :
# #     # Retrieve the normalized depth image
# #     zed.retrieve_image(image_depth_zed, sl.VIEW.DEPTH)
# #     # Use get_data() to get the numpy array
# #     image_depth_ocv = image_depth_zed.get_data()
# #     # Display the depth view from the numpy array
# #     cv2.imshow("Image", image_depth_ocv)


# # #accessing depth values
# # print(depth_map.get_value(100,100));

# # #displaying the depth image
# # # you have to do this because it needs to change from 32-bit depth map to 
# # # a 8 bit greyscale depth image
# # depth_for_display = sl.Mat()
# # zed.retrieve_image(depth_for_display, sl.VIEW.DEPTH)


# # # depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_frame_array, alpha = 0.04), cv2.COLORMAP_JET)# this puts a color efffect on the depth frame
# # # images = depth_colormap                              # use this for individual streams
# # images = depth_for_display
# # cv2.namedWindow('Align Example', cv2.WINDOW_NORMAL)   # names and shows the streams
# # cv2.imwrite('depthmap.jpg', images)

# # # # if you press escape or q you can cancel the process
# # key = cv2.waitKey(1)
# # print("press escape to cancel")
# # if key & 0xFF == ord('q') or key == 27:
# #     cv2.destroyAllWindows()


# zed.close()


import sys
import numpy as np
import pyzed.sl as sl
import cv2

def main() :

    # Create a ZED camera object
    zed = sl.Camera()

    # Set configuration parameters
    init = sl.InitParameters()
    init.camera_resolution = sl.RESOLUTION.HD1080
    init.camera_fps = 30
    init.depth_mode = sl.DEPTH_MODE.PERFORMANCE
    init.coordinate_units = sl.UNIT.MILLIMETER

    # Open the camera
    err = zed.open(init)
    if err != sl.ERROR_CODE.SUCCESS :
        print(repr(err))
        zed.close()
        exit(1)

    # Set runtime parameters after opening the camera
    runtime = sl.RuntimeParameters()
    runtime.sensing_mode = sl.SENSING_MODE.STANDARD

    # Prepare new image size to retrieve half-resolution images
    image_size = zed.get_camera_information().camera_resolution
    image_size.width = image_size.width /2
    image_size.height = image_size.height /2

    # Declare your sl.Mat matrices
    image_zed = sl.Mat(image_size.width, image_size.height, sl.MAT_TYPE.U8_C4)
    depth_image_zed = sl.Mat(image_size.width, image_size.height, sl.MAT_TYPE.U8_C4)

    key = ' '
    while key != 113 :
        err = zed.grab(runtime)
        if err == sl.ERROR_CODE.SUCCESS :
            # Retrieve the left image, depth image in the half-resolution
            color_frame = zed.retrieve_image(image_zed, sl.VIEW.LEFT, sl.MEM.CPU, image_size)
            zed.retrieve_image(depth_image_zed, sl.VIEW.DEPTH, sl.MEM.CPU, image_size)
            # Retrieve the RGBA point cloud in half resolution

            # To recover data from sl.Mat to use it with opencv, use the get_data() method
            # It returns a numpy array that can be used as a matrix with opencv
            image_ocv = image_zed.get_data()
            depth_image_ocv = depth_image_zed.get_data()
        
            # color_frame = frame.retrieve_image(sl.VIEW.LEFT, sl.MEM.CPU)
            # color_image = color_frame.get_data()
            # depth_frame = frame.retrieve_image(sl.VIEW.DEPTH, sl.MEM.CPU)
            # depth_image = depth_frame.get_data()

            # print(image_ocv)
            cv2.imshow("Image", image_ocv)
            cv2.imshow("Depth", depth_image_ocv)

            key = cv2.waitKey(10)


    cv2.destroyAllWindows()
    zed.close()

    print("\nFINISH")

if __name__ == "__main__":
    main()