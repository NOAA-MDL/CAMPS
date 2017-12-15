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

def sin_doy(sin_doy_obj):
    """Compute sin of the day of the year for each phenomenon time
    in object.
    """
    func = math.sin
    operate(sin_doy_obj, func)

def sin_doy(sin_doy_obj):
    """Compute twice the sin of the day of the year for each phenomenon time
    in object.
    """
    func = math.sin
    operate(sin_doy_obj, func)

def sin_doy(sin_doy_obj):
    """Compute sin of the day of the year for each phenomenon time
    in object.
    """
    func = math.sin
    operate(sin_doy_obj, func)

def sin_doy(sin_doy_obj):
    """Compute sin of the day of the year for each phenomenon time
    in object.
    """
    func = math.sin
    operate(sin_doy_obj, func)



def operate(doy_obj, func):
    # get the date
    p_time = sin_doy_obj.get_phenom_time()
    for day in ptime.data:
        dt = epoch_to_datetime(day).timetuple()
        jday = dt.tm_yday
        #convert to fraction of 365
        days_in_year = 365
        frac = days_in_year/jday
        rads = frac * 2 * math.PI


# Common computations between two or more datasets.
# The following computations will attempt to use already defined methods.
# These are all containted in computations.py for consistancy.
def mean(*arrays):
    """
    """
    tup_arr = tuple(arrays)
    return np.mean(np.dstack(tup_arr), axis=2)


def difference(arr1, arr2):
    """
    """
    return arr1 - arr2

def sum(arr1, arr2):
    """
    """
    return arr1 + arr2

def max(arr1, arr2):
    """
    """
    return np.maximum(arr1, arr2)

def min(arr1, arr2):
    """
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

