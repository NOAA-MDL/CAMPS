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

def sin_doy(time, pred):
    """Compute sin of the day of the year for each phenomenon time
    in object.
    """
    sin_doy_obj = Wisps_data('doy')
    leadTime = pred.leadTime
    l_time_obj = Time.LeadTime(start_time=leadTime, end_time=leadTime)
    f_time = time
    f_time_obj = Time.ForecastReferenceTime(start_time=p_time, end_time=p_time)
    p_time_obj = Time.PhenomenonTime(start_time=p_time+f_time, end_time=f_time+p_time)
    sin_doy_obj.time.append(l_time_obj, f_time_obj, p_time_obj)
    func = math.sin
    out = operate(sin_doy_obj, func)
    return out

def sin_2doy(time, pred):
    """Compute twice the sin of the day of the year for each phenomenon time
    in object.
    """
    sin_doy_obj = Wisps_data('doy')
    leadTime = pred.leadTime
    l_time_obj = Time.LeadTime(start_time=leadTime, end_time=leadTime)
    f_time = time
    f_time_obj = Time.ForecastReferenceTime(start_time=f_time, end_time=f_time)
    p_time_obj = Time.PhenomenonTime(start_time=leadTime+f_time, end_time=f_time+leadTime)
    sin_doy_obj.time = [l_time_obj, f_time_obj, p_time_obj]
    func = math.sin
    out = operate(sin_doy_obj, func, 2)
    return out

def cos_doy(time, pred):
    """Compute cos of the day of the year for each phenomenon time
    in object.
    """
    cos_doy_obj = Wisps_data('doy')
    leadTime = pred.leadTime
    l_time_obj = Time.LeadTime(start_time=leadTime, end_time=leadTime)
    f_time = time
    f_time_obj = Time.ForecastReferenceTime(start_time=p_time, end_time=p_time)
    p_time_obj = Time.PhenomenonTime(start_time=p_time+f_time, end_time=f_time+p_time)
    cos_doy_obj.time.append(l_time_obj, f_time_obj)
    func = math.cos
    out = operate(cos_doy_obj, func)
    return out

def cos_2doy(time, pred):
    """Compute cos of the day of the year for each phenomenon time
    in object.
    """
    cos_doy_obj = Wisps_data('doy')
    leadTime = pred.leadTime
    l_time_obj = Time.LeadTime(start_time=leadTime, end_time=leadTime)
    p_time = time
    f_time_obj = Time.ForecastReferenceTime(start_time=p_time, end_time=p_time)
    p_time_obj = Time.PhenomenonTime(start_time=p_time+f_time, end_time=f_time+p_time)
    cos_doy_obj.time.append(l_time_obj, f_time_obj)
    func = math.cos
    out = operate(cos_doy_obj, func, 2)
    return out



def operate(doy_obj, func, multiplyer=1):
    # get the date
    p_time = doy_obj.get_phenom_time()
    for day in p_time.data: # should just iterate once
        dt = epoch_to_datetime(day).timetuple()
        jday = dt.tm_yday
        #convert to fraction of 365
        days_in_year = 365
        frac = days_in_year/jday
        rads = frac * 2 * math.pi
        out = func(multiplyer * rads)
        doy_obj.data = np.hstack((doy_obj.data, np.array([out])))
    return doy_obj


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

