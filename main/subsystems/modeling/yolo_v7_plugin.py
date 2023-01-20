import ctypes
import os
import shutil
import random
import sys
import threading
import time
import cv2
import numpy as np
import torch
from torchvision import transforms
from torchvision.ops import nms

from toolbox.globals import print, time_synchronized


class Yolov7(object):
    """
    description: A YOLOv7 class that wraps initialization, preprocess and postprocess ops.
    """

    def __init__(self, repo_filepath, model_filepath, input_dimension, acceleration):
        # config check
        assert acceleration in ['tensor_rt', 'gpu', None]
        self.acceleration = acceleration

        self.input_w = self.input_h = input_dimension

        # load model locally
        self.model = torch.hub.load(
            repo_filepath, 'custom', model_filepath, source='local')

        self.tensor_transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Resize((self.input_w, self.input_h)),
        ])

        if acceleration == 'gpu' and torch.cuda.is_available():
            print("[modeling]   gpu_acceleration: ENABLED\n")
            # loaded_model = loaded_model.to(torch.device("cuda"))
            self.device = torch.device("cuda")
        else:
            print("[modeling]   Running on CPU\n")
            self.device = torch.device("cpu")

        self.model = self.model.to(self.device)

        self.model.zero_grad(set_to_none=True)
        self.model.eval()
        torch.no_grad()

    def preprocess_image(self, image_pre):
        # takes in (h, w, c) BGR image
        image_post = cv2.cvtColor(image_pre, cv2.COLOR_BGR2RGB)
        image_tensor = self.tensor_transform(image_post)
        image_tensor = image_tensor.unsqueeze(0)
        return image_tensor, image_pre, image_pre.shape[0], image_pre.shape[1]

    @torch.no_grad()
    def infer(self, image_tensor):
        start = time_synchronized()
        try:
            # transfer image to device
            tensor_input = image_tensor.to(self.device)
            layer_outputs = self.model(tensor_input)[0]
        except Exception as error:
            print(error)
        end = time_synchronized()
        return layer_outputs, end - start

    def non_max_suppression(self, prediction, conf_thresh=0.25, nms_thresh=0.4):
        """
        description: Removes detections with lower object confidence score than 'conf_thresh' and performs
        Non-Maximum Suppression to further filter detections.
        param:
            prediction: detections, (x1, y1, x2, y2, conf, cls_id)
            image_h: original image height
            image_w: original image width
            conf_thresh: a confidence threshold to filter detections
            nms_thresh: a iou threshold to filter detections
        return:
            boxes: output after nms with the shape (x1, y1, x2, y2, conf, cls_id)
        """
        nc = prediction.shape[2] - 5  # number of classes
        xc = prediction[..., 4] > conf_thresh  # candidates

        output = [torch.zeros((0, 6), device=prediction.device)
                  ] * prediction.shape[0]

        mi = 5 + nc  # mask start index

        for x in prediction:
            x = x[xc[0]]  # confidence

            if not x.shape[0]:
                continue

            # Compute conf
            x[:, 5:] *= x[:, 4:5]  # conf = obj_conf * cls_conf

            # Box (center x, center y, width, height) to (x1, y1, x2, y2)
            box = self.xywh2xyxy(x[:, :4])

            # Detections matrix nx6 (xyxy, conf, cls)
            conf, j = x[:, 5:].max(1, keepdim=True)
            x = torch.cat((box, conf, j.float()), 1)[
                conf.view(-1) > conf_thresh]

            n = x.shape[0]  # number of boxes
            if not n:  # no boxes
                continue

            c = x[:, 5:6] * (self.input_h)  # classes
            # boxes (offset by class), scores
            boxes, scores = x[:, :4] + c, x[:, 4]

            i = nms(boxes, scores, nms_thresh)  # NMS
            output[0] = x[i]
        return output

    def xywh2xyxy(self, x):
        # Convert nx4 boxes from [x, y, w, h] to [x1, y1, x2, y2] where xy1=top-left, xy2=bottom-right
        y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
        y[:, 0] = x[:, 0] - x[:, 2] / 2  # top left x
        y[:, 1] = x[:, 1] - x[:, 3] / 2  # top left y
        y[:, 2] = x[:, 0] + x[:, 2] / 2  # bottom right x
        y[:, 3] = x[:, 1] + x[:, 3] / 2  # bottom right y
        return y

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
