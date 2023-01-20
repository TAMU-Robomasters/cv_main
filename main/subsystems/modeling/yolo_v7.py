# library imports
import numpy as np
import cv2
import os
import time
from super_map import LazyDict
import torch

# project imports
from toolbox.globals import path_to, absolute_path_to, config, print, runtime, time_synchronized
from toolbox.geometry_tools import BoundingBox, Position

#
# config
#
hardware_acceleration = config.model.hardware_acceleration
input_dimension = config.model.input_dimension
which_model = config.model.which_model

# config check
assert hardware_acceleration in ['tensor_rt', 'gpu', None]

#
#
# helpers
#
#


def init_yolo_v7(model):
    print("\n[modeling] YOLO v7 loading")

    loaded_model = None

    if hardware_acceleration == 'tensor_rt':
        print("[modeling]   tensor_rt: ENABLED\n")

        from subsystems.modeling.yolo_v7_trt_plugin import Yolov7TRT

        # create YoloV7TRT object
        model.yolov7_trt = Yolov7TRT(
            path_to.yolo_v7.tensor_rt_engine, path_to.yolo_v7.tensor_rt_plugin)

        _, infer_time = model.yolov7_trt.infer_warmup()

        print(f"[modeling]  warmup time: {infer_time:.2f} ms")

        model.get_bounding_boxes = lambda *args, **kwargs: yolo_v7_tensor_rt_bounding_boxes(
            model, *args, **kwargs)

    else:
        from subsystems.modeling.yolo_v7_plugin import Yolov7

        if not os.path.exists(path_to.yolo_v7.path_to_folder):
            raise Exception(
                f"yolov7 repo not found at {path_to.yolo_v7.path_to_folder}")
        if not os.path.exists(path_to.yolo_v7.pytorch_model):
            raise Exception(
                f"model not found at {path_to.yolo_v7.pytorch_model}")

        # config check
        assert hardware_acceleration in ['tensor_rt', 'gpu', None]

        # create Yolov7 object
        model.yolov7 = Yolov7(repo_filepath=path_to.yolo_v7.path_to_folder,
                              model_filepath=path_to.yolo_v7.pytorch_model,
                              input_dimension=config.model.input_dimension,
                              acceleration=config.model.hardware_acceleration)

        # export data
        model.net = model.yolov7.model
        model.get_bounding_boxes = lambda *args, **kwargs: yolo_v7_beta_bounding_boxes(
            model, *args, **kwargs)


@torch.no_grad()
def yolo_v7_bounding_boxes(model, frame, minimum_confidence, threshold):
    # NOTE: this code is derived from https://www.pyimagesearch.com/2018/11/12/yolo-object-detection-with-opencv/
    t0 = time_synchronized()

    # initialize our lists of detected bounding boxes, confidences, and class IDs, respectively
    boxes = []
    confidences = []
    class_ids = []

    if model.W is None or model.H is None:
        (model.H, model.W) = frame.shape[:2]

    labels = []

    t1 = time_synchronized()

    try:
        layer_outputs = model.net(frame)
        t2 = time_synchronized()
        labels = layer_outputs.xyxy[0]
    except Exception as error:
        print(error)

    # loop over each of the detections
    if not isinstance(labels, list):
        labels = labels.cpu()
    for detection in labels:
        x_top_left, y_top_left, x_bottom_right, y_bottom_right, box_confidence, class_id = detection

        # filter out weak predictions
        if box_confidence > minimum_confidence:
            boxes.append(
                BoundingBox.from_points(
                    top_left=(x_top_left, y_top_left),
                    bottom_right=(x_bottom_right, y_bottom_right),
                )
            )
            confidences.append(float(box_confidence))
            class_ids.append(class_id)

    t3 = time_synchronized()

    print(f"\n\npreprocess: {t1-t0:.3f} ms")
    print(f"inference: {t2-t1:.3f} ms")
    print(f"postprocess: {t3-t2:.3f} ms")

    return boxes, confidences, class_ids


def yolo_v7_beta_bounding_boxes(model, frame, minimum_confidence, threshold):
    t0 = time_synchronized()

    image_tensor, image_pre, image_h, image_w = model.yolov7.preprocess_image(
        frame)

    t1 = time_synchronized()

    inf_output, inf_time = model.yolov7.infer(image_tensor)

    t2 = time_synchronized()

    outputs = model.yolov7.non_max_suppression(
        inf_output, conf_thresh=0.25, nms_thresh=0.20)

    t3 = time_synchronized()

    raw_boxes = outputs[0][:, :4]
    confidences = outputs[0][:, 4]
    class_ids = outputs[0][:, 5]

    rescaled_boxes = model.yolov7.rescale_coords_to_original(
        image_h, image_w, raw_boxes)

    # print(boxes, confs, classes)

    boxes = [BoundingBox.from_points(
        top_left=(x1, y1), bottom_right=(x2, y2)) for x1, y1, x2, y2 in rescaled_boxes]

    t4 = time_synchronized()

    # print(f"\n\npreprocess: {t1 - t0:.3f} s")
    # print(f"inference: {t2 - t1:.3f} s")
    # print(f"nms: {t3 - t2:.3f} s")
    # print(f"postprocess: {t4 - t3:.3f} s")

    return boxes, confidences, class_ids


def yolo_v7_tensor_rt_bounding_boxes(model, frame, minimum_confidence, threshold):
    # initialize our lists of detected bounding boxes, confidences, and class IDs, respectively
    boxes = []
    confidences = []
    class_ids = []

    start = time.time()

    # run inference
    output, inftime = model.yolov7_trt.infer(frame)

    # print(f"frame shape {frame.shape}")
    boxes, confidences, class_ids = model.yolov7_trt.postprocess_results(
        output, image_h=frame.shape[0], image_w=frame.shape[1])

    # print(boxes, confidences, class_ids)
    boxes = [BoundingBox.from_points(
        top_left=(x1, y1), bottom_right=(x2, y2)) for x1, y1, x2, y2 in boxes]

    end = time.time()

    print(f"[modeling]  inf time: {(inftime)*1000:.2f} ms")
    print(f"[modeling]  bbx time: {(end - start)*1000:.2f} ms")

    return boxes, confidences, class_ids
