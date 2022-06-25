import scipy
from scipy import stats
from scipy.optimize import curve_fit
from random import random, sample, choices
import statistics
import math
import numpy

def create_function_of_time(times, values):
    def rsquared(x, y):
        """ Return R^2 where x and y are array-like."""
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        return r_value**2
    
    def polynomial(x, a, b, c):
        return a * x + b * x**2 + c
    
    # draw a line
    coefficient, intercept = numpy.polyfit(times, values, 1)
    
    function_of_time = lambda time: coefficient * time + intercept
    confidence_of_fit = rsquared(times, values)
    
    return function_of_time, confidence_of_fit


# dummy values for testing
# times = [1656125803.885474, 1656125804.251055, 1656125804.428928, 1656125804.58773, 1656125804.757615, 1656125804.9278579, 1656125805.080042, 1656125805.2393138, 1656125805.3969789, 1656125805.672342, 1656125805.8693728, 1656125806.111021, 1656125806.3862479, 1656125806.5845299]
# values = [[926.5, 662.0], [911.0, 661.0], [910.5, 661.0], [893.0, 658.5], [877.0, 657.0], [861.5, 654.5], [846.0, 655.5], [834.0, 655.5], [819.5, 655.5], [807.0, 655.5], [799.0, 656.5], [796.5, 656.0], [794.0, 657.5], [793.5, 658.0]]

class LinearPredictor:
    """
        predictor = Predictor()
        predictor.add_data(time=0, point=[ 20, 20+random() ])
        predictor.add_data(time=1, point=[ 25, 21+random() ])
        predictor.add_data(time=2, point=[ 29, 22+random() ])
        predictor.add_data(time=3, point=[ 35, 23+random() ])
        predictor.add_data(time=4, point=[ 30, 22.5+random() ])
        predictor.predict_next()
    """
    
    def __init__(self, buffer_size=math.inf):
        self.buffer_size = buffer_size
        self.times = []
        self.values = []
    
    def add_data(self, *, time, values):
        self.times.append(time)
        self.values.append(values)
        # restrict to a buffer size
        if self.buffer_size != math.inf:
            self.times = self.times[-self.buffer_size:]
            self.values = self.values[-self.buffer_size:]
    
    def predict_next(self, timesteps=1):
        value_stacks = zip(*self.values)
        confidences = []
        
        next_value = []
        next_timestep = self.times[-1] + (self.get_timestep_size() * timesteps)
        for each_value_stack in value_stacks:
            func_of_time, confidence = create_function_of_time(self.times, each_value_stack)
            confidences.append(confidence)
            next_value.append(func_of_time(next_timestep))
        
        total_confidence = statistics.mean(confidences)
        return next_value, total_confidence, confidences
    
    def get_timestep_size(self):
        # get pairwise elements
        return statistics.median(tuple(
            each - prev for prev, each in zip(self.times[0:-1], self.times[1:])
        ))
    
    def reset(self):
        self.times = self.times[-1:]
        self.values = self.values[-1:]
    
    def __len__(self):
        return len(self.times)



Predictor = LinearPredictor