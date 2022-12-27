import numpy as np

class Position(list):
    @property
    def x(self): return self[0]
    
    @x.setter
    def x(self, value): self[0] = value
    
    @property
    def y(self): return self[1]
    
    @y.setter
    def y(self, value): self[1] = value
    
    @property
    def z(self): return self[2]
    
    @z.setter
    def z(self, value): self[2] = value
    
    def __repr__(self):
        if len(self) >= 3:
            return f'(x={self.x},y={self.y},z={self.z})'
        elif len(self) == 2:
            return f'(x={self.x},y={self.y})'
        elif len(self) == 1:
            return f'(x={self.x})'
        else:
            return '[]'

class BoundingBox(list):
    """
    x_top_left, y_top_left, width, height format
    """
    
    @classmethod
    def from_points(cls, *, top_left, bottom_right):
        top_left = Position(top_left)
        bottom_right = Position(bottom_right)
        width  = abs(top_left.x - bottom_right.x)
        height = abs(top_left.y - bottom_right.y)
        return BoundingBox([ top_left.x, top_left.y, width, height ])
    
    @property
    def x_top_left(self): return self[0]
    
    @x_top_left.setter
    def x_top_left(self, value): self[0] = value
    
    @property
    def y_top_left(self): return self[1]
    
    @y_top_left.setter
    def y_top_left(self, value): self[1] = value
    
    @property
    def x_bottom_right(self): return self.x_top_left + self.width
    
    @property
    def y_bottom_right(self): return self.y_top_left + self.height
    
    @property
    def width(self): return self[2]
    
    @width.setter
    def width(self, value): self[2] = value
    
    @property
    def height(self): return self[3]
    
    @height.setter
    def height(self, value): self[3] = value
    
    @property
    def center(self):
        return Position([
            self.x_top_left + (self.width / 2),
            self.y_top_left + (self.height / 2),
        ])
    
    @property
    def area(self):
        return self.width * self.height
    
    def contains(self, point):
        point = Position(point)
        return (
            self.x_top_left     < point.x and
            self.x_bottom_right > point.x and
            self.y_top_left     < point.y and
            self.y_bottom_right > point.y
        )
        
    def __repr__(self):
        return f'[x_top_left={f"{self.x_top_left:.2f}".rjust(5)},y_top_left={f"{self.y_top_left:.2f}".rjust(5)},width={f"{self.width:.2f}".rjust(5)},height={f"{self.height:.2f}".rjust(5)}]'

class Geometry():
    @classmethod
    def bounds_to_points(self, max_x, max_y, min_x, min_y):
        return (min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, min_y)
    
    @classmethod
    def bounding_box(self, array_of_points):
        """
        @array_of_points
            the input needs to be an array of tuples (x,y)
            the array can be any number of points
        returns:
            max_x, max_y, min_x, min_y
        """
        max_x = -float('Inf')
        max_y = -float('Inf')
        min_x = float('Inf')
        min_y = float('Inf')
        for each in array_of_points:
            if max_x < each[0]:
                max_x = each[0]
            if max_y < each[1]:
                max_y = each[1]
            if min_x > each[0]:
                min_x = each[0]
            if min_y > each[1]:
                min_y = each[1]
        return max_x, max_y, min_x, min_y
    
    @classmethod
    def poly_area(self, points):
        """
        @points: a list of points (x,y tuples) that form a polygon
        
        returns: the area of the polygon
        """
        xs = []
        ys = []
        for each in points:
            x,y = each
            xs.append(x)
            ys.append(y)
        return 0.5*np.abs(np.dot(xs,np.roll(ys,1))-np.dot(ys,np.roll(xs,1)))


    @classmethod
    def distance_between(self, point1, point2):
        x1,y1 = point1
        x2,y2 = point2
        dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)  
        return dist  

    @classmethod
    def rotate(self, point, angle, about):
        """
        @about a tuple (x,y) as a point, this is the point that will be used as the axis of rotation
        @point a tuple (x,y) as a point that will get rotated counter-clockwise about the origin
        @angle an angle in radians, the amount of counter-clockwise roation

        The angle should be given in radians.
        """
        ox, oy = about
        px, py = point

        qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
        qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
        return qx, qy
    
    @classmethod
    def counter_clockwise_angle(self, from_, to):
        x1, y1 = from_
        x2, y2 = to
        answer = math.atan2(x1*y2-y1*x2,x1*x2+y1*y2)
        # if negative, change to positive and add 180 degrees
        if answer < 0:
            answer = answer * -1 + math.pi
        return answer
    
    @classmethod
    def vector_pointing(self, from_, to):
        return tuple(map(int.__sub__, to, point))
