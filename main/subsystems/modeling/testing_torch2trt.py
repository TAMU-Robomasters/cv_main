from toolbox.globals import path_to, absolute_path_to, config, print
import numpy # Dont delete - uses our numpy version isntead of torch's
import torch

model = torch.hub.load('ultralytics/yolov5', 'custom', path=path_to.yolov5_pt)

from torch2trt import torch2trt

x = torch.ones((1, 3, config.model.input_dimension, config.model.input_dimension)).cuda()
model_trt = torch2trt(model, [x])

# save
torch.save(model, f'{__file__}.trt.model')