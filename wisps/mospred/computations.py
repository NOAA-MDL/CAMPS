import os
import sys
import re
import pdb
import metpy.calc as calc
from metpy.units import units
import math
import numpy as np
import operator
relative_path = os.path.abspath(
    os.path.dirname(os.path.realpath(__file__)) + "/..")
sys.path.insert(0, relative_path)
from data_mgmt.fetch import *
from data_mgmt.Time import epoch_to_datetime
import data_mgmt.Time as Time
from data_mgmt.Wisps_data import Wisps_data


def cos(w_obj):
    """
    Take the cos of all values in the data of the Wisps_data object.
    """
    w_obj.data = np.cos(w_obj.data)


def sin(w_obj):
    """
    Take the sin of all values in the data of the Wisps_data object.
    """
    w_obj.data = np.sin(w_obj.data)

def tan(w_obj):
    """
    Take the tan of all values in the data of the Wisps_data object.
    """
    w_obj.data = np.tan(w_obj.data)

def multipy(w_obj, scalar):
    """Multiplies n Wisps_data object's data by a scalar
    """
    w_obj.data = w_obj.data * scalar

def divide(w_obj, scalar):
    """Divides n Wisps_data object's data by a scalar
    """
    w_obj.data = w_obj.data / scalar

# Common computations between two or more datasets.
# The following computations will attempt to use already defined methods.
# These are all containted in computations.py for consistancy.

def mean(*arrays):
    """Calculates the mean accross cells of each array along second axis.
    """
    tup_arr = tuple(arrays)
    return np.mean(np.dstack(tup_arr), axis=2)

def difference(arr1, arr2):
    """Calculates difference between two arrays.
    """
    return arr1 - arr2

def sum(arr1, arr2):
    """Calculates sum of two arrays by cell.
    """
    return arr1 + arr2

def max(arr1, arr2):
    """Calculates the maximum value of each cell 
    """
    return np.maximum(arr1, arr2)

def min(arr1, arr2):
    """Calculates the minimum value of each cell 
    """
    return np.minimum(arr1, arr2)

    #TODO
def point(arr1, arr2):
    """
    """
    pass

def mid_range(arr1, arr2):
    """
    """
    pass

def standard_deviation(arr1, arr2):
    """
    """
    pass

def variance(arr1, arr2):
    """
    """
    pass

def mult(arr1, arr2):
    """
    """
    pass

