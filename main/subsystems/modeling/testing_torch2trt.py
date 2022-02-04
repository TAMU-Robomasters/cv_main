from torch2trt import torch2trt
import torch
from torchvision.models.alexnet import alexnet
model = alexnet(pretrained=True).eval().cuda()
x = torch.ones((1, 3, 224, 224)).cuda()
model_trt = torch2trt(model, [x])

# save
torch.save(model, f'{__file__}.trt.model')