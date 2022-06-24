import numpy
import cv2
# project imports 
from toolbox.globals import path_to, config, print
from toolbox.file_system_tools import FS

rgb = lambda red,blue,green: tuple((red, green, blue))
rgb_to_bgr = lambda red,blue,green: tuple((blue, green, red)) # <- cause cv2 is dumb

red    = rgb(240, 113, 120)
cyan   = rgb(137, 221, 255)
blue   = rgb(130, 170, 255)
green  = rgb(195, 232, 141)
yellow = rgb(254, 195,  85)

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
    
    @property
    def in_cv2_format(self):
        return self.img
    
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
        cv2.waitKey(1) # doesn't actually wait
    
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

    def with_points(self, array_of_points, color=yellow, radius=3):
        color = rgb_to_bgr(*color)
        img_copy = self.img.copy()
        for x, y, in array_of_points:
            # I believe thickness=-1 means the object should be filled
            cv2.circle(img_copy, (x, y), radius, color, thickness=-1, lineType=8, shift=0)
        return Image(img_copy)
    
    def add_point(self, *, x, y, color=yellow, radius=3):
        color = rgb_to_bgr(*color)
        self.img = cv2.circle(self.img, (int(x), int(y)), radius, tuple(int(each) for each in color), thickness=-1, lineType=8, shift=0)
        return self
    
    def rotated_180_degrees(self):
        return Image(cv2.rotate(self.img, cv2.ROTATE_180))
    
    def rotate_180_degrees(self):
        self.img = cv2.rotate(self.img, cv2.ROTATE_180)
        return self
    
    def add_bounding_box(self, bounding_box, color=green, thickness=2):
        """
        @bounding_box:
            should be (x, y, width, height)
            the x,y should be the top-left corner of the image
            y=0 is the very top of the image
            x=0 is the left-most side of the image
        @color: tuple of RGB values, each are 0-255
        @thickness: int of how many pixels
        """
        color = rgb_to_bgr(*color)
        
        # Starting cordinate
        start = (int (bounding_box[0]), int(bounding_box[1]))
        # Bottom right of the bounding box
        end = (int(bounding_box[0] + bounding_box[2]), int(bounding_box[1] + bounding_box[3]))

        # Draw bounding box on image
        self.img = cv2.rectangle(self.img, start, end, color, thickness)
        return self

    def add_text(self, *, text, location, color=(255, 255, 255), size=0.7):
        color = rgb_to_bgr(*color)
        font = cv2.FONT_HERSHEY_SIMPLEX
        line_type = 2
        self.img = cv2.putText(self.img, text, location, font, size, color, line_type)
        return self