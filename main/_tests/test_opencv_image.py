import cv2
# relative imports
from toolbox.globals import PATHS

# read image 
print("about to read an image")
img = cv2.imread(PATHS["main_test_image"])
print("just read an image")
# show image
cv2.imshow('Example - Show image in window',img)
 
cv2.waitKey(0) # waits until a key is pressed
cv2.destroyAllWindows() # destroys the window showing image