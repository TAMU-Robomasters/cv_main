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

# def is_iterable(thing):
#     # https://stackoverflow.com/questions/1952464/in-python-how-do-i-determine-if-an-object-is-iterable
#     try:
#         iter(thing)
#     except TypeError:
#         return False
#     else:
#         return True

# import torch
# import numpy    
# def to_tensor(an_object):
#     # if already a tensor, just return
#     if isinstance(an_object, torch.Tensor):
#         return an_object
#     # if numpy, just convert
#     if numpy and isinstance(an_object, numpy.ndarray):
#         return torch.from_numpy(an_object).float()
    
#     # if scalar, wrap it with a tensor
#     if not is_iterable(an_object):
#         return torch.tensor(an_object)
#     else:
#         # fastest (by a lot) way to convert list of numpy elements to torch tensor
#         try:
#             return torch.from_numpy(numpy.stack(an_object)).float()
#         except Exception as error:
#             pass
#         # if all tensors of the same shape
#         try:
#             return torch.stack(tuple(an_object), dim=0)
#         except Exception as error:
#             pass
#         # if all scalar tensors
#         try:
#             return torch.tensor(tuple(an_object))
#         except Exception as error:
#             pass
        
#         # 
#         # convert each element, and make sure its not a generator
#         # 
#         converted_data = tuple(to_tensor(each) for each in an_object)
#         # now try try again 
        
#         # if all tensors of the same shape
#         try:
#             return torch.stack(tuple(an_object), dim=0)
#         except Exception as error:
#             pass
#         # if all scalar tensors
#         try:
#             return torch.tensor(tuple(an_object))
#         except Exception as error:
#             pass
#         # 
#         # fallback: reshape to fit (give error if too badly mishapen)
#         # 
#         size_mismatch = False
#         biggest_number_of_dimensions = 0
#         non_one_dimensions = None
#         # check the shapes of everything
#         for tensor in converted_data:
#             skipping = True
#             each_non_one_dimensions = []
#             for index, each_dimension in enumerate(tensor.shape):
#                 # keep track of number of dimensions
#                 if index+1 > biggest_number_of_dimensions:
#                     biggest_number_of_dimensions += 1
                    
#                 if each_dimension != 1:
#                     skipping = False
#                 if skipping and each_dimension == 1:
#                     continue
#                 else:
#                     each_non_one_dimensions.append(each_dimension)
            
#             # if uninitilized
#             if non_one_dimensions is None:
#                 non_one_dimensions = list(each_non_one_dimensions)
#             # if dimension already exists
#             else:
#                 # make sure its the correct shape
#                 if non_one_dimensions != each_non_one_dimensions:
#                     size_mismatch = True
#                     break
        
#         if size_mismatch:
#             sizes = "\n".join([ f"    {tuple(each.shape)}" for each in converted_data])
#             raise Exception(f'When converting an object to a torch tensor, there was an issue with the shapes not being uniform. All shapes need to be the same, but instead the shapes were:\n {sizes}')
        
#         # make all the sizes the same by filling in the dimensions with a size of one
#         reshaped_list = []
#         for each in converted_data:
#             shape = tuple(each.shape)
#             number_of_dimensions = len(shape)
#             number_of_missing_dimensions = biggest_number_of_dimensions - number_of_dimensions 
#             missing_dimensions_tuple = (1,)*number_of_missing_dimensions
#             reshaped_list.append(torch.reshape(each, (*missing_dimensions_tuple, *shape)))
        
#         return torch.stack(reshaped_list).type(torch.float)

# def opencv_image_to_torch_image(array):
#     # 1, 210, 160, 3 => 1, 3, 210, 160
#     tensor = to_tensor(array)
#     dimension_count = len(tensor.shape)
#     new_shape = [ each for each in range(dimension_count) ]
#     height = new_shape[-3]
#     width = new_shape[-2]
#     channels = new_shape[-1]
#     new_shape[-3] = channels
#     new_shape[-2] = height
#     new_shape[-1] = width
#     return tensor.permute(*new_shape)

# def torch_image_to_opencv_image(array):
#     # 1, 3, 210, 160 => 1, 210, 160, 3
#     tensor = to_tensor(array)
#     dimension_count = len(tensor.shape)
#     new_shape = [ each for each in range(dimension_count) ]
#     channels = new_shape[-3]
#     height = new_shape[-2]
#     width = new_shape[-1]
#     new_shape[-3] = height  
#     new_shape[-2] = width   
#     new_shape[-1] = channels
#     return tensor.permute(*new_shape)