import os
import sys
import re
import pdb
import metpy.calc as calc
from metpy.units import units
import math
import numpy as np
import operator

from ..core.fetch import *
from ..core.Time import epoch_to_datetime
from ..core import Time as Time
from ..core.Camps_data import Camps_data


"""Module: computations.py
This module contains various mathematical and statistical
operations to perform on the data of camps data objects.

Methods:
    cos
    sin
    tan
    sum
    difference
    multiply
    divide
    mean
    max
    min
"""


def cos(w_obj):
    """Cosine of each element in the data array of the Camps_data object"""

    w_obj.data = np.cos(w_obj.data)


def sin(w_obj):
    """Sine of each element in the data array of the Camps_data object"""

    w_obj.data = np.sin(w_obj.data)


def tan(w_obj):
    """Tangent of each element in the data array of the Camps_data object"""

    w_obj.data = np.tan(w_obj.data)


def sum(arr1, arr2):
    """Element-wise sum of two arrays of identical dimensions"""

    ndim = len(arr1.shape)
    assert(len(arr2.shape) == ndim), \
        "computations.sum: arr1, arr2 do not match number of dimensions."
    for i,n in enumerate(arr1.shape):
        assert(arr2.shape[i] == n), \
            "computations.sum: size of a dimension in arr1, arr2 does not match."

    return arr1 + arr2


def difference(arr1, arr2):
    """Element-wise subtraction of array arr2 from array arr1, where 
    these arrays have identical dimensions.
    """

    ndim = len(arr1.shape)
    assert(len(arr2.shape) == ndim), \
        "computations.sum: arr1, arr2 do not match number of dimensions."
    for i,n in enumerate(arr1.shape):
        assert(arr2.shape[i] == n), \
            "computations.sum: size of a dimension in arr1, arr2 does not match."

    return arr1 - arr2


def multiply(w_obj, scalar):
    """Multiplication by a scalar each value in the data of the Camps_data object"""

    w_obj.data = w_obj.data * float(scalar)


def divide(w_obj, scalar):
    """Division by a non-zero scalar each value in the data of the  Camps_data object"""

    if scalar != 0:
        w_obj.data = w_obj.data / float(scalar)


# Common computations between two or more datasets.
# The following computations will attempt to use already defined methods.
# These are all containted in computations.py for consistancy.

def mean(*arrays):
    """Calculates the mean across cells of each array along second axis."""

    tup_arr = tuple(arrays)
    return np.mean(np.dstack(tup_arr), axis=2)


def max(arr1, arr2):
    """Calculates the maximum value of each cell"""

    return np.maximum(arr1, arr2)


def min(arr1, arr2):
    """Calculates the minimum value of each cell"""

    return np.minimum(arr1, arr2)
