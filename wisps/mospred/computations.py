import os
import sys
import re
import pdb
relative_path = os.path.abspath(
    os.path.dirname(os.path.realpath(__file__)) + "/..")
sys.path.insert(0, relative_path)
from data_mgmt.fetch import *
import metpy.calc as calc
from metpy.units import units
import math
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





