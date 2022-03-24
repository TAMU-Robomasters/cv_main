from toolbox.globals import path_to, config, print

import numpy as np
np.random.seed(42)

# 
# setup labels and colors
#
MODEL_LABELS = open(path_to.model_labels).read().strip().split("\n")
MODEL_COLORS = np.random.randint(0, 255, size = (len(MODEL_LABELS), 3), dtype = "uint8")
COLOR_GREEN  = (0, 255, 0)
COLOR_YELLOW = (255, 255, 00)