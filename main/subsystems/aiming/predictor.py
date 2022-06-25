import scipy
from scipy.optimize import curve_fit
from random import random, sample, choices
import statistics
import math

def create_function_of_time(times, values):
    def linear(time, a, b, c):
        return a * time + b
    
    def rsquared(x, y):
        """ Return R^2 where x and y are array-like."""
        slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(x, y)
        return r_value**2
    
    def polynomial(x, a, b, c):
        return a * x + b * x**2 + c
    
    (a, b, c), _ = curve_fit(objective, times, values)
    function_of_time = lambda time: linear(time, a, b, c)
    confidence_of_fit = rsquared(times, values)
    
    return function_of_time, confidence_of_fit


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
    
    def predict_next(self):
        value_stacks = zip(*self.values)
        confidences = []
        
        next_value = []
        timestep_size = self.get_timestep_size()
        for each_value_stack in value_stacks:
            func_of_time, confidence = create_function_of_time(self.times, each_value_stack)
            confidences.append(confidence)
            next_value.append(func_of_time(timestep_size))
        
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