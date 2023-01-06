import ctypes
import os
import shutil
import random
import sys
import threading
import time
import cv2
import numpy as np
import pycuda.autoinit
import pycuda.driver as cuda
import tensorrt as trt
import torch
from torchvision.ops import nms

from toolbox.globals import print


class Yolov7TRT(object):
    """
    description: A YOLOv7 class that warps TensorRT ops, preprocess and postprocess ops.
    """

    def __init__(self, engine_filepath, plugin_filepath):
        # load plugin
        ctypes.CDLL(plugin_filepath)

        # Create a CUDA context
        self.cuda_ctx = cuda.Device(0).make_context()
        stream = cuda.Stream()
        TRT_LOGGER = trt.Logger(trt.Logger.INFO)
        runtime = trt.Runtime(TRT_LOGGER)

        # Deserialize TRT engine from file
        with open(engine_filepath, "rb") as f:
            engine = runtime.deserialize_cuda_engine(f.read())
        context = engine.create_execution_context()

        host_inputs = []
        cuda_inputs = []
        host_outputs = []
        cuda_outputs = []
        bindings = []

        for binding in engine:
            print('binding:', binding, engine.get_binding_shape(binding))
            size = trt.volume(engine.get_binding_shape(
                binding)) * engine.max_batch_size
            dtype = trt.nptype(engine.get_binding_dtype(binding))
            # Allocate host and device buffers
            host_mem = cuda.pagelocked_empty(size, dtype)
            cuda_mem = cuda.mem_alloc(host_mem.nbytes)
            # Append the device buffer to device bindings.
            bindings.append(int(cuda_mem))
            # Append to the appropriate list.
            if engine.binding_is_input(binding):
                self.input_w = engine.get_binding_shape(binding)[-1]
                self.input_h = engine.get_binding_shape(binding)[-2]
                host_inputs.append(host_mem)
                cuda_inputs.append(cuda_mem)
            else:
                host_outputs.append(host_mem)
                cuda_outputs.append(cuda_mem)

        # print(f"output size: {engine.get_binding_shape('prob')[0]}")

        # Store
        self.stream = stream
        self.context = context
        self.engine = engine
        self.host_inputs = host_inputs
        self.cuda_inputs = cuda_inputs
        self.host_outputs = host_outputs
        self.cuda_outputs = cuda_outputs
        self.bindings = bindings
        self.batch_size = engine.max_batch_size

    def preprocess_image(self, image_pre):
        # takes in (h, w, c) BGR image
        image_post = cv2.cvtColor(image_pre, cv2.COLOR_BGR2RGB)
        image_post = cv2.resize(image_post, (self.input_w, self.input_h))
        image_post = image_post.transpose((2, 0, 1)).astype(np.float16) / 255.0
        image_post = np.ascontiguousarray(image_post)
        return image_post, image_pre, image_pre.shape[0], image_pre.shape[1]

    def postprocess_results(self, output, image_h, image_w):
        # output: (6001, 1, 1)
        output = output[:self.engine.get_binding_shape('prob')[0]]

        num_found = int(output[0])

        pred = np.reshape(output[1:], (-1, 6))[:num_found, :]

        # Trandform bbox from [center_x, center_y, w, h] to [x1, y1, x2, y2]
        pred[:, :4] = self.xywh2xyxy(image_h, image_w, pred[:, :4])

        # Torchvision NMS
        x1y1x2y2 = torch.tensor(pred[:, :4])
        scores = torch.tensor(pred[:, 4])
        keep = nms(x1y1x2y2, scores, 0.2)
        pred = np.take(pred, keep.numpy(), axis=0)

        if len(pred):  # if there are any boxes
            pred[:, :4] = self.rescale_coords_to_original(
                image_h, image_w, pred[:, :4])
            boxes = pred[:, :4]
            confs = pred[:, 4]
            classes = pred[:, 5]
            return boxes, confs, classes
        else:
            return np.array([]), np.array([]), np.array([])

    def infer_warmup(self, warmup_image=None):

        if warmup_image == None:
            warmup_image = np.zeros(
                [self.input_h, self.input_w, 3], dtype=np.uint8)

        threading.Thread.__init__(self)
        # Make self the active context, pushing it on top of the context stack.
        self.cuda_ctx.push()
        # Restore
        stream = self.stream
        context = self.context
        engine = self.engine
        host_inputs = self.host_inputs
        cuda_inputs = self.cuda_inputs
        host_outputs = self.host_outputs
        cuda_outputs = self.cuda_outputs
        bindings = self.bindings

        print(f"batch size: {self.batch_size}")
        # Do image preprocess

        start = time.time()
        image_post, image_pre, image_h, image_w = self.preprocess_image(
            warmup_image)

        # Copy input image to host buffer
        np.copyto(host_inputs[0], image_post.ravel())
        # Transfer input data  to the GPU.
        cuda.memcpy_htod_async(cuda_inputs[0], host_inputs[0], stream)
        # Run inference.
        context.execute_async(batch_size=self.batch_size,
                              bindings=bindings, stream_handle=stream.handle)
        # Transfer predictions back from the GPU.
        cuda.memcpy_dtoh_async(host_outputs[0], cuda_outputs[0], stream)
        # Synchronize the stream
        stream.synchronize()
        # Remove any context from the top of the context stack, deactivating it.
        self.cuda_ctx.pop()

        end = time.time()
        # No postprocess
        return image_post, end - start

    def infer(self, image_raw):
        threading.Thread.__init__(self)
        # Make self the active context, pushing it on top of the context stack.
        self.cuda_ctx.push()
        # Restore
        stream = self.stream
        context = self.context
        engine = self.engine
        host_inputs = self.host_inputs
        cuda_inputs = self.cuda_inputs
        host_outputs = self.host_outputs
        cuda_outputs = self.cuda_outputs
        bindings = self.bindings

        start = time.time()
        # Do image preprocess
        image_post, image_pre, image_h, image_w = self.preprocess_image(
            image_raw)
        end = time.time()

        # Copy input image to host buffer
        np.copyto(host_inputs[0], image_post.ravel())

        # Transfer input data to the GPU.
        cuda.memcpy_htod_async(cuda_inputs[0], host_inputs[0], stream)
        # Run inference.
        context.execute_async(batch_size=self.batch_size,
                              bindings=bindings, stream_handle=stream.handle)
        # Transfer predictions back from the GPU.
        cuda.memcpy_dtoh_async(host_outputs[0], cuda_outputs[0], stream)
        # Synchronize the stream
        stream.synchronize()
        # Remove any context from the top of the context stack, deactivating it.
        self.cuda_ctx.pop()
        # Here we use the first row of output in that batch_size = 1
        return host_outputs[0], end - start

    def non_max_suppression(self, prediction, image_h, image_w, conf_thres=0.25, nms_thres=0.4):
        """
        description: Removes detections with lower object confidence score than 'conf_thres' and performs
        Non-Maximum Suppression to further filter detections.
        param:
            prediction: detections, (x1, y1, x2, y2, conf, cls_id)
            image_h: original image height
            image_w: original image width
            conf_thres: a confidence threshold to filter detections
            nms_thres: a iou threshold to filter detections
        return:
            boxes: output after nms with the shape (x1, y1, x2, y2, conf, cls_id)
        """
        # Get the boxes that score > CONF_THRESH
        boxes = prediction[prediction[:, 4] >= conf_thres]
        # Trandform bbox from [center_x, center_y, w, h] to [x1, y1, x2, y2]
        boxes[:, :4] = self.xywh2xyxy(image_h, image_w, boxes[:, :4])
        # clip the coordinates
        boxes[:, 0] = np.clip(boxes[:, 0], 0, image_w - 1)
        boxes[:, 1] = np.clip(boxes[:, 1], 0, image_h - 1)
        boxes[:, 2] = np.clip(boxes[:, 2], 0, image_w - 1)
        boxes[:, 3] = np.clip(boxes[:, 3], 0, image_h - 1)
        # Object confidence
        confs = boxes[:, 4]
        # Sort by the confs
        boxes = boxes[np.argsort(-confs)]
        # Perform non-maximum suppression
        keep_boxes = []
        while boxes.shape[0]:
            large_overlap = self.bbox_iou(np.expand_dims(
                boxes[0, :4], 0), boxes[:, :4]) > nms_thres
            label_match = boxes[0, -1] == boxes[:, -1]
            # Indices of boxes with lower confidence scores, large IOUs and matching labels
            invalid = large_overlap & label_match
            keep_boxes += [boxes[0]]
            boxes = boxes[~invalid]
        boxes = np.stack(keep_boxes, 0) if len(keep_boxes) else np.array([])
        return boxes

    def rescale_coords_to_original(self, image_h, image_w, boxes):
        """
        description:    Rescale the coordinates of the boxes from model size to image size
        param:
            image_h:   height of original image
            image_w:   width of original image
            boxes:     A boxes numpy, each row is a box [x1, y1, x2, y2]
        return:
            boxes:     A boxes numpy, each row is a box [x1, y1, x2, y2]
        """
        h_rescaler = image_h / self.input_h
        w_rescaler = image_w / self.input_w

        boxes[:, 0] = boxes[:, 0] * w_rescaler
        boxes[:, 1] = boxes[:, 1] * h_rescaler
        boxes[:, 2] = boxes[:, 2] * w_rescaler
        boxes[:, 3] = boxes[:, 3] * h_rescaler
        return boxes

    def xywh2xyxy(self, image_h, image_w, x):
        """
        description:    Convert nx4 boxes from [x, y, w, h] to [x1, y1, x2, y2] where xy1=top-left, xy2=bottom-right
        param:
            image_h:   height of original image
            image_w:   width of original image
            x:          A boxes numpy, each row is a box [center_x, center_y, w, h]
        return:
            y:          A boxes numpy, each row is a box [x1, y1, x2, y2]
        """
        # write function here
        y = np.zeros_like(x)
        y[:, 0] = x[:, 0] - x[:, 2] / 2
        y[:, 1] = x[:, 1] - x[:, 3] / 2
        y[:, 2] = x[:, 0] + x[:, 2] / 2
        y[:, 3] = x[:, 1] + x[:, 3] / 2
        return y

    def bbox_iou(self, box1, box2, x1y1x2y2=True):
        """
        description: compute the IoU of two bounding boxes
        param:
            box1: A box coordinate (can be (x1, y1, x2, y2) or (x, y, w, h))
            box2: A box coordinate (can be (x1, y1, x2, y2) or (x, y, w, h))            
            x1y1x2y2: select the coordinate format
        return:
            iou: computed iou
        """
        if not x1y1x2y2:
            # Transform from center and width to exact coordinates
            b1_x1, b1_x2 = box1[:, 0] - box1[:, 2] / \
                2, box1[:, 0] + box1[:, 2] / 2
            b1_y1, b1_y2 = box1[:, 1] - box1[:, 3] / \
                2, box1[:, 1] + box1[:, 3] / 2
            b2_x1, b2_x2 = box2[:, 0] - box2[:, 2] / \
                2, box2[:, 0] + box2[:, 2] / 2
            b2_y1, b2_y2 = box2[:, 1] - box2[:, 3] / \
                2, box2[:, 1] + box2[:, 3] / 2
        else:
            # Get the coordinates of bounding boxes
            b1_x1, b1_y1, b1_x2, b1_y2 = box1[:,
                                              0], box1[:, 1], box1[:, 2], box1[:, 3]
            b2_x1, b2_y1, b2_x2, b2_y2 = box2[:,
                                              0], box2[:, 1], box2[:, 2], box2[:, 3]

        # Get the coordinates of the intersection rectangle
        inter_rect_x1 = np.maximum(b1_x1, b2_x1)
        inter_rect_y1 = np.maximum(b1_y1, b2_y1)
        inter_rect_x2 = np.minimum(b1_x2, b2_x2)
        inter_rect_y2 = np.minimum(b1_y2, b2_y2)
        # Intersection area
        inter_area = np.clip(inter_rect_x2 - inter_rect_x1 + 1, 0, None) * \
            np.clip(inter_rect_y2 - inter_rect_y1 + 1, 0, None)
        # Union Area
        b1_area = (b1_x2 - b1_x1 + 1) * (b1_y2 - b1_y1 + 1)
        b2_area = (b2_x2 - b2_x1 + 1) * (b2_y2 - b2_y1 + 1)

        iou = inter_area / (b1_area + b2_area - inter_area + 1e-16)

        return iou
