import cv2
import os
import datetime
# relative imports
from toolbox.video_tools import Video
from toolbox.globals import PATHS, config, print
import pyzed.sl as zed
import numpy as np

videostream = config.videostream
aiming      = config.aiming

class VideoStream:
    def __init__(self):
        self.video_output = None
        if videostream.testing.record_interval > 0:
            self.video_output = self.begin_video_recording()

        self.camera = zed.Camera()
        # TODO - make these params dependent on config. is the format something we need to worry about? (int8 vs ...)
        init_params = zed.InitParameters()
        init_params.camera_resolution = zed.RESOLUTION.HD720
        init_params.camera_fps = aiming.stream_framerate
        init_params.depth_mode = zed.DEPTH_MODE.PERFORMANCE
        init_params.coordinate_units = zed.UNIT.METER
        # Use a right-handed Y-up coordinate system
        init_params.coordinate_system = zed.COORDINATE_SYSTEM.RIGHT_HANDED_Y_UP 
        # TODO - customize runtime params with config
        self.runtime_parameters = zed.RuntimeParameters()

        err = self.camera.open(init_params)
        while err != zed.ERROR_CODE.SUCCESS:
            print('VideoStream: Failed to open ZED camera! Retrying...')
            err = self.camera.open(init_params)
        
        # Create an RGB sl.Mat object with int8
        self.image_zed = zed.Mat(self.camera.get_camera_information().camera_resolution.width, 
            self.camera.get_camera_information().camera_resolution.height, zed.MAT_TYPE.U8_C3)
        # Create a sl.Mat with float type (32-bit)
        self.depth_zed = zed.Mat(self.camera.get_camera_information().camera_resolution.width, 
            self.camera.get_camera_information().camera_resolution.height, zed.MAT_TYPE.F32_C1)

        # Enable positional tracking with default parameters
        py_transform = zed.Transform()  # First create a Transform object for TrackingParameters object
        tracking_parameters = zed.PositionalTrackingParameters(_init_pos=py_transform)

        # Set previous area file
        # tracking_parameters.area_file_path = "filename.area"

        # Supposed to set intial pos to 0,0,0, comment if doesnt work
        initial_position = zed.Transform()
        initial_translation = zed.Translation()
        initial_translation.init_vector(0,0,0)
        initial_position.set_translation(initial_translation)
        tracking_parameters.set_initial_world_transform(initial_position)

        err = zed.enable_positional_tracking(tracking_parameters)
        if err != zed.ERROR_CODE.SUCCESS:
            exit(1)

        # Track the camera position during 1000 frames
        self.zed_pose = zed.Pose()
        self.zed_sensors = zed.SensorsData()
    
    def frames(self):
        """
        Returns a generator that outputs color and depth frames. Save the frames on the fly if video recording is enabled.

        Input: None
        Output: A generator which will produce color and depth images at each step.
        """
        frame_number = 0
        # retry after failure
        while True:
            while self.camera.grab(self.runtime_parameters) == zed.ERROR_CODE.SUCCESS:
                frame_number += 1
                # TODO - if using depth and left camera view, have to reconcile them with an additional transformation
                self.camera.retrieve_image(self.image_zed, zed.VIEW.LEFT)
                self.camera.retrieve_measure(self.depth_zed, zed.MEASURE.DEPTH)

                # Get the pose of the left eye of the camera with reference to the world frame
                self.camera.get_position(self.zed_pose, zed.REFERENCE_FRAME.WORLD)
                self.camera.get_sensors_data(self.zed_sensors, zed.TIME_REFERENCE.IMAGE)
                zed_imu = self.zed_sensors.get_imu_data()

                # Display the translation and timestamp
                py_translation = zed.Translation()
                tx = round(self.zed_pose.get_translation(py_translation).get()[0], 3)
                ty = round(self.zed_pose.get_translation(py_translation).get()[1], 3)
                tz = round(self.zed_pose.get_translation(py_translation).get()[2], 3)
                print("Translation: Tx: {0}, Ty: {1}, Tz {2}, Timestamp: {3}\n".format(tx, ty, tz, self.zed_pose.timestamp.get_milliseconds()))

                # Display the orientation quaternion
                py_orientation = zed.Orientation()
                ox = round(self.zed_pose.get_orientation(py_orientation).get()[0], 3)
                oy = round(self.zed_pose.get_orientation(py_orientation).get()[1], 3)
                oz = round(self.zed_pose.get_orientation(py_orientation).get()[2], 3)
                ow = round(self.zed_pose.get_orientation(py_orientation).get()[3], 3)
                print("Orientation: Ox: {0}, Oy: {1}, Oz {2}, Ow: {3}\n".format(ox, oy, oz, ow))
                
                #Display the IMU acceleratoin
                acceleration = [0,0,0]
                zed_imu.get_linear_acceleration(acceleration)
                ax = round(acceleration[0], 3)
                ay = round(acceleration[1], 3)
                az = round(acceleration[2], 3)
                print("IMU Acceleration: Ax: {0}, Ay: {1}, Az {2}\n".format(ax, ay, az))
                
                #Display the IMU angular velocity
                a_velocity = [0,0,0]
                zed_imu.get_angular_velocity(a_velocity)
                vx = round(a_velocity[0], 3)
                vy = round(a_velocity[1], 3)
                vz = round(a_velocity[2], 3)
                print("IMU Angular Velocity: Vx: {0}, Vy: {1}, Vz {2}\n".format(vx, vy, vz))

                # Display the IMU orientation quaternion
                zed_imu_pose = zed.Transform()
                ox = round(zed_imu.get_pose(zed_imu_pose).get_orientation().get()[0], 3)
                oy = round(zed_imu.get_pose(zed_imu_pose).get_orientation().get()[1], 3)
                oz = round(zed_imu.get_pose(zed_imu_pose).get_orientation().get()[2], 3)
                ow = round(zed_imu.get_pose(zed_imu_pose).get_orientation().get()[3], 3)
                print("IMU Orientation: Ox: {0}, Oy: {1}, Oz {2}, Ow: {3}\n".format(ox, oy, oz, ow))


                # Convert images to ocv format, remove alpha channel
                color_image = self.image_zed.get_data()[:,:,:3]
                depth_image = self.depth_zed.get_data()
                # Add frame to video recording based on recording frequency
                if self.video_output and (frame_number % videostream.testing.record_interval == 0):
                    print(" saving_frame:",frame_number)
                    self.video_output.write(color_image)
#                 cv2.imshow('img', depth_image)
#                 cv2.waitKey(100)
                yield color_image, depth_image
            if config.mode == 'development':
                print("VideoStream: unable to retrieve frame.")
                print('(retrying)')
        
    def __del__(self):
        print("Closing ZED camera")

        # Save arena file
        print("Saving arena file")
        zed.disable_positional_tracking("filename.area")

        self.camera.close()
    
    # TODO - another option for ZED is to use SVO instead of a collection of video frames.
    # If we want to record with SVO, we cannot also use the camera in "live" mode.
    # The benefit of SVO is that it fakes all zed sensors if we want to replay it in a testing env.
    def begin_video_recording(self):
        """
        Run live video recording using nvenc.

        Input: None
        Output: Video object to add frames too.
        """

        color_video_location = PATHS.record_video_output_color
        
        # Setup video output path based on date and counter
        c = 1
        file_path = color_video_location.replace(".do_not_sync",datetime.datetime.now().strftime("%Y-%m-%d")+"_"+str(c)+".do_not_sync")
        while os.path.isfile(file_path):
            c += 1
            file_path = color_video_location.replace(".do_not_sync",datetime.datetime.now().strftime("%Y-%m-%d")+"_"+str(c)+".do_not_sync")

        # Start up video output
        gst_out = "appsrc ! video/x-raw, format=BGR ! queue ! videoconvert ! video/x-raw,format=BGRx ! nvvidconv ! nvv4l2h264enc ! h264parse ! matroskamux ! filesink location="+file_path
        video_output = cv2.VideoWriter(gst_out, cv2.CAP_GSTREAMER, 0, float(aiming.framerate), (int(aiming.stream_width), int(aiming.stream_height)))
        if not video_output.isOpened():
            print("Failed to open output")

        return video_output    
    
    def save_video_if_needed(self):
        # Save video output
        if self.video_output:
            print("Saving Recorded Video")
            self.video_output.release()
            print("Finished Saving Video")
