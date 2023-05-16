import numpy
import cv2
# project imports 
from toolbox.globals import print
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
        try:
            self.img = cv2.circle(self.img, (int(x), int(y)), radius, tuple(int(each) for each in color), thickness=-1, lineType=8, shift=0)
        except Exception as error:
            print(f"error doing .add_point() on image. Probably out of bounds: x={x},y={y}")
        return self
    
    def rotated_180_degrees(self):
        return Image(cv2.rotate(self.img, cv2.ROTATE_180))
    
    def rotate_180_degrees(self):
        self.img = cv2.rotate(self.img, cv2.ROTATE_180)
        return self
    
    @property
    def hsv(self):
        # Convert the BRG image to RGB
        hsv = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV)
        return hsv
    
    def from_hsv(self, value):
        self.img = cv2.cvtColor(value, cv2.COLOR_HSV2BGR)
        return self
    
    def shift_hue(self, amount):
        img = self.img
        img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        max_value_of_pixel = 256
        
        # make hue the first layer
        img = numpy.moveaxis(img, 2, 0)
        img[0] += int(amount) % max_value_of_pixel
        img[0] += numpy.array( (img[0] >= max_value_of_pixel) * -max_value_of_pixel ).astype(numpy.dtype('uint8')) # keep within bounds
        # then put it back
        img = numpy.moveaxis(img, 0, 2)
        
        self.img = cv2.cvtColor(img, cv2.COLOR_HSV2BGR)
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

# import Image
# import numpy as np

# def rgb_to_hsv(rgb):
#     # Translated from source of colorsys.rgb_to_hsv
#     # r,g,b should be a numpy arrays with values between 0 and 255
#     # rgb_to_hsv returns an array of floats between 0.0 and 1.0.
#     rgb = rgb.astype('float')
#     hsv = np.zeros_like(rgb)
#     # in case an RGBA array was passed, just copy the A channel
#     hsv[..., 3:] = rgb[..., 3:]
#     r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
#     maxc = np.max(rgb[..., :3], axis=-1)
#     minc = np.min(rgb[..., :3], axis=-1)
#     hsv[..., 2] = maxc
#     mask = maxc != minc
#     hsv[mask, 1] = (maxc - minc)[mask] / maxc[mask]
#     rc = np.zeros_like(r)
#     gc = np.zeros_like(g)
#     bc = np.zeros_like(b)
#     rc[mask] = (maxc - r)[mask] / (maxc - minc)[mask]
#     gc[mask] = (maxc - g)[mask] / (maxc - minc)[mask]
#     bc[mask] = (maxc - b)[mask] / (maxc - minc)[mask]
#     hsv[..., 0] = np.select(
#         [r == maxc, g == maxc], [bc - gc, 2.0 + rc - bc], default=4.0 + gc - rc)
#     hsv[..., 0] = (hsv[..., 0] / 6.0) % 1.0
#     return hsv

# def hsv_to_rgb(hsv):
#     # Translated from source of colorsys.hsv_to_rgb
#     # h,s should be a numpy arrays with values between 0.0 and 1.0
#     # v should be a numpy array with values between 0.0 and 255.0
#     # hsv_to_rgb returns an array of uints between 0 and 255.
#     rgb = np.empty_like(hsv)
#     rgb[..., 3:] = hsv[..., 3:]
#     h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
#     i = (h * 6.0).astype('uint8')
#     f = (h * 6.0) - i
#     p = v * (1.0 - s)
#     q = v * (1.0 - s * f)
#     t = v * (1.0 - s * (1.0 - f))
#     i = i % 6
#     conditions = [s == 0.0, i == 1, i == 2, i == 3, i == 4, i == 5]
#     rgb[..., 0] = np.select(conditions, [v, q, p, p, t, v], default=v)
#     rgb[..., 1] = np.select(conditions, [v, v, v, q, p, p], default=t)
#     rgb[..., 2] = np.select(conditions, [v, p, t, v, v, q], default=p)
#     return rgb.astype('uint8')


# def shift_hue(arr,hout):
#     hsv=rgb_to_hsv(arr)
#     hsv[...,0]=hout
#     rgb=hsv_to_rgb(hsv)
#     return rgb

# img = Image.open('tweeter.png').convert('RGBA')
# arr = np.array(img)

# if __name__=='__main__':
#     green_hue = (180-78)/360.0
#     red_hue = (180-180)/360.0

#     new_img = Image.fromarray(shift_hue(arr,red_hue), 'RGBA')
#     new_img.save('tweeter_red.png')

#     new_img = Image.fromarray(shift_hue(arr,green_hue), 'RGBA')
#     new_img.save('tweeter_green.png')