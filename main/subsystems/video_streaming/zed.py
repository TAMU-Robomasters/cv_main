import cv2
import os
import datetime
import pyzed.sl as zed
import numpy as np
# relative imports
from toolbox.video_tools import Video
from toolbox.globals import path_to, config, print, runtime

videostream = config.videostream
aiming      = config.aiming

class VideoStream:
    def __init__(self):
        self.video_output = None
        self.camera = None
        if videostream.testing.record_interval > 0:
            self.video_output = self.begin_video_recording()

        init_params = zed.InitParameters(sdk_verbose=True)
        self.camera = zed.Camera()
        init_params.sdk_cuda_ctx_     = runtime.tensorrt_context
        # init_params.camera_fps        = aiming.stream_framerate # attempting to fix this: https://community.stereolabs.com/t/zed-tensorrt-problems-invalidating-cuda-context-handle/1099/3
        init_params.camera_resolution = getattr(zed.RESOLUTION, config.zed.resolution)
        init_params.depth_mode        = getattr(zed.DEPTH_MODE, config.zed.depth_mode)
        init_params.coordinate_units  = getattr(zed.UNIT      , config.zed.unit      )
        
        err = self.camera.open(init_params)
        while err != zed.ERROR_CODE.SUCCESS:
            print('VideoStream: Failed to open ZED camera! Retrying...')
            err = self.camera.open(init_params)
        
        # not sure if this is doing what we want it to do
        self.camera.set_camera_settings(zed.VIDEO_SETTINGS.BRIGHTNESS, config.zed.calibration.brightness)
        self.camera.set_camera_settings(zed.VIDEO_SETTINGS.CONTRAST,   config.zed.calibration.contrast  )
        self.camera.set_camera_settings(zed.VIDEO_SETTINGS.HUE,        config.zed.calibration.hue       )
        self.camera.set_camera_settings(zed.VIDEO_SETTINGS.SATURATION, config.zed.calibration.saturation)
        self.camera.set_camera_settings(zed.VIDEO_SETTINGS.SHARPNESS,  config.zed.calibration.sharpness )
        self.camera.set_camera_settings(zed.VIDEO_SETTINGS.GAMMA,      config.zed.calibration.gamma     )
        self.camera.set_camera_settings(zed.VIDEO_SETTINGS.GAIN,       config.zed.calibration.gain      )
        self.camera.set_camera_settings(zed.VIDEO_SETTINGS.EXPOSURE,   config.zed.calibration.exposure  )

        # TODO - customize runtime params with config
        self.runtime_parameters = zed.RuntimeParameters()
        
        # Create an RGB sl.Mat object with int8
        self.image_zed = zed.Mat(
            self.camera.get_camera_information().camera_resolution.width, 
            self.camera.get_camera_information().camera_resolution.height,
            # TODO - make these params dependent on config. is the format something we need to worry about? (int8 vs ...)
            zed.MAT_TYPE.U8_C3
        )
        # Create a sl.Mat with float type (32-bit)
        self.depth_zed = zed.Mat(
            self.camera.get_camera_information().camera_resolution.width, 
            self.camera.get_camera_information().camera_resolution.height,
            zed.MAT_TYPE.F32_C1
        )
    
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
                self.camera.retrieve_image(self.image_zed, zed.VIEW.RIGHT)
                self.camera.retrieve_measure(self.depth_zed, zed.MEASURE.DEPTH)
                # Convert images to ocv format, remove alpha channel
                color_image = np.array(self.image_zed.get_data()[:,:,:3])
                depth_image = np.array(self.depth_zed.get_data())
                # Add frame to video recording based on recording frequency
                if self.video_output and (frame_number % videostream.testing.record_interval == 0):
                    print(" saving_frame:",frame_number)
                    self.video_output.write(color_image)
                # cv2.imshow('img', depth_image)
                # cv2.waitKey(100)
                yield frame_number, color_image, depth_image
            if config.mode == 'development':
                print("VideoStream: unable to retrieve frame.")
                print('(retrying)')
        
    def __del__(self):
        if self.camera:
            print("Closing ZED camera")
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

        color_video_location = path_to.record_video_output_color
        
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
