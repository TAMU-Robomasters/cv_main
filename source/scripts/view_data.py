import numpy as np
from toolbox.globals import ENVIRONMENT, PATHS, PARAMETERS, print

depthfileLocation = PATHS['record_file_output_depth']

arr = np.load(depthfileLocation+'2.npy').reshape(848,480)
print(arr)