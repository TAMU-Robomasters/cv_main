import torch
import torch.nn as nn
from torch2trt import torch2trt

class TestNetwork(torch.nn.Module):
    def __init__(self, **config):
        super(TestNetwork, self).__init__()
        # 
        # options
        # 
        self.input_shape     = config.get('input_shape'    , (1, 28, 28))
        self.output_shape    = config.get('output_shape'   , (2,))
        self.lr              = config.get('lr'             , 0.01)
        self.momentum        = config.get('momentum'       , 0.5 )
        
        # 
        # layers
        # 
        self.layers = nn.Sequential()
        self.layers.add_module('conv1', nn.Conv2d(1, 10, kernel_size=5))
        self.layers.add_module('conv1_pool', nn.MaxPool2d(2))
        self.layers.add_module('conv1_activation', nn.ReLU())
        self.layers.add_module('conv2', nn.Conv2d(10, 10, kernel_size=5))
        self.layers.add_module('conv2_drop', nn.Dropout2d())
        self.layers.add_module('conv2_pool', nn.MaxPool2d(2))
        self.layers.add_module('conv2_activation', nn.ReLU())
        self.layers.add_module('flatten', nn.Flatten(1)) # 1 => skip the first dimension because thats the batch dimension
        # self.layers.add_module('fc1', nn.Linear(self.size_of_last_layer, product(self.output_shape)))
        self.layers.add_module('fc1_activation', nn.LogSoftmax(dim=1))
        
        # 
        # support (optimizer, loss)
        # 
        # create an optimizer
        self.optimizer = torch.optim.SGD(self.parameters(), lr=self.lr, momentum=self.momentum)
    
    def loss_function(self, model_output, ideal_output):
        # convert from one-hot into number, and send tensor to device
        ideal_output = from_onehot_batch(ideal_output).to(self.device)
        return F.nll_loss(model_output, ideal_output)

    def forward(self, input_data):
        return self.layers.forward(input_data)


a =  TestNetwork()