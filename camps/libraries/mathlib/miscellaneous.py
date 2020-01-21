import os
import sys
import pdb
import numpy as np

from ...core.fetch import *
from ...core.Time import epoch_to_datetime
from ...core import Time as Time
from ...core import Camps_data
from ...mospred import util
from ...registry import util as cfg

def DOY(time, pred):
    """
    Compute the day of year based on the forecast time and lead time.
    The result will include fractional days, such that 6z would equal .25 days.
    """
    # Create the empty object
    doy_obj = Camps_data('day_of_year')

    # Set dimension as size of station
    station_length = len(util.read_valid_stations(None))
    
    doy_obj.dimensions.append(cfg.read_dimensions()['nstations'])
    # Create time objects
    lead_time = pred.leadTime
    fcst_time = time
    phenom_time = lead_time + fcst_time
    lead_time_obj = Time.LeadTime(start_time=lead_time, end_time=lead_time)
    fcst_time_obj = Time.ForecastReferenceTime(start_time=fcst_time, end_time=fcst_time)
    phenom_time_obj = Time.PhenomenonTime(start_time=phenom_time, end_time=phenom_time)
    doy_obj.time.extend((lead_time_obj, fcst_time_obj, phenom_time_obj))
    # Caluclate DOY
    dt = epoch_to_datetime(phenom_time)
    jday = dt.timetuple().tm_yday
    hours = dt.hour
    days = jday + (hours/24)
    doy_obj.data = np.array([days]*(station_length))
    return doy_obj

