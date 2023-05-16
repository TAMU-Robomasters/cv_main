import numpy

from collections.abc import Iterable
def flatten(l):
    for el in l:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el

def ndarray_to_list(ndarray):
    if type(ndarray) != numpy.ndarray:
        return ndarray
    else:
        as_list = ndarray.tolist()
        new_list = []
        for each in as_list:
            new_list.append(ndarray_to_list(each))
        return new_list



import math
def average(items):
    running_total = 0
    for each in items:
        running_total += each
    return running_total / len(items)