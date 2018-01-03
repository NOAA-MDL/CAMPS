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

def DOY(time, pred):
    """
    Compute the day of year based on the forecast time and lead time.
    The result will include fractional days, such that 6z would equal .25 days.
    """
    # Create the empty object
    doy_obj = Wisps_data('doy')
    # Create time objects
    lead_time = pred.leadTime
    fcst_time = time
    phenom_time = lead_time + fcst_time
    lead_time_obj = Time.LeadTime(start_time=lead_time, end_time=lead_time)
    fcst_time_obj = Time.ForecastReferenceTime(start_time=fcst_time, end_time=fcst_time)
    phenom_time_obj = Time.PhenomenonTime(start_time=phenom_time, end_time=phenom_teim)
    sin_doy_obj.time.append(lead_time_obj, fcst_time_obj, phenom_time_obj)
    # Caluclate DOY
    dt = epoch_to_datetime(phenom_time).timetuple()
    jday = dt.tm_yday
    hours = dt.hour
    days = jday + (hours/24)
    doy_obj.data = np.array([days])
    return doy_obj

