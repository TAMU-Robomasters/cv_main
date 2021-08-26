import numpy
import cv2
# relative imports 
from toolbox.globals import COLOR_GREEN, COLOR_YELLOW
from toolbox.file_system_tools import FS

class Image(object):
    def __init__(self, arg1):
        """
        @arg1: can either be a string (the path to an image file) or an ndarray (a cv2 image)
        """
        if type(arg1) == str:
            self.path = arg1
            self.img = cv2.imread(arg1)
        elif type(arg1) == numpy.ndarray:
            self.path = None
            self.img = arg1
        else:
            raise Exception('Not sure how to create an image using ' + str(arg1))
    
    def save(self, to, image_type="png"):
        FS.makedirs(FS.dirname(to))
        result = cv2.imwrite(FS.absolute_path(to+"."+image_type), self.img)
        if not result:
            raise Exception("Could not save image:"+str(to))
        
    def show(self, name=None):
        """
        this will open the image in a GUI but allow the code to keep executing
        """
        print("Press ESC (on the image window) to exit the image")
        if self.path != None:
            name = self.path
        elif name is None:
            name = "img"
        cv2.imshow(name, self.img)
    
    def show_and_pause(self, name=None):
        """
        this will open the image in a GUI and wait for the user to press
        the escape key before resuming code execution
        """
        print("Press ESC (on the image window) to exit the image")
        if self.path != None:
            name = self.path
        elif name is None:
            name = "img"
        cv2.imshow(name, self.img)
        while True:
            key = cv2.waitKey(1)
            if key == 27:  #ESC key to break
                break
        cv2.destroyWindow(name)

    def with_points(self, array_of_points, color=COLOR_YELLOW, radius=3):
        img_copy = self.img.copy()
        for x, y, in array_of_points:
            # I believe thickness=-1 means the object should be filled
            cv2.circle(img_copy, (x, y), radius, color, thickness=-1, lineType=8, shift=0)
        return Image(img_copy)
    
    def add_bounding_box(self, bounding_box, color=COLOR_GREEN, thickness=2):
        """
        @bounding_box:
            should be (x, y, width, height)
            the x,y should be the top-left corner of the image
            y=0 is the very top of the image
            x=0 is the left-most side of the image
        @color: tuple of RGB values, each are 0-255
        @thickness: int of how many pixels
        """
        
        # Starting cordinate
        start = (int (bounding_box[0]), int(bounding_box[1]))
        # Bottom right of the bounding box
        end = (int(bounding_box[0] + bounding_box[2]), int(bounding_box[1] + bounding_box[3]))

        # Draw bounding box on image
        self.img = cv2.rectangle(self.img, start, end, color, thickness)
        return self


def add_text(*, image, text, location):
    font = cv2.FONT_HERSHEY_SIMPLEX 
    bottom_left_corner_of_text = (10,10) 
    font_scale = .7
    font_color = (255,255,255) 
    line_type = 2
    return cv2.putText(image, text, location, font, font_scale, font_color, line_type)