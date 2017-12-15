import os
import sys
import re
import pdb
relative_path = os.path.abspath(
    os.path.dirname(os.path.realpath(__file__)) + "/..")
sys.path.insert(0, relative_path)
import numpy as np
from data_mgmt.fetch import fetch
from math import *


def WSpd_setup(time, predictor):
    """
    """
    #print "time is ", time
    #pdb.set_trace()
    predictor.change_property('Uwind')
    u_wind = fetch(time,**predictor.search_metadata)
    predictor.change_property('Vwind')
    v_wind = fetch(time,**predictor.search_metadata)
    wspd_arr = wind_speed(u_wind.data, v_wind.data)
    # new pointer named wspd to reduce confusion
    wspd = v_wind 
    # Replace on of the wind objects with calculated arr
    wspd.data = wspd_arr


    return wspd

def wind_speed(u_wind, v_wind):
    """
    """
    wspd = np.sqrt(u_wind**2 + v_wind**2)
    return wspd
