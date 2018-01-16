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





def temp_corr_setup(temp, pred):
    """Compute temperature coreection.
    """
    # Only will work if surface or 2m elevation
    level = pred.get_coordinate()
    if level != 2 or level is not None:
        raise ValueError("level is not surface or 2m")
    # Otherwise, will work on sigma surface and isobarametric surfaces
    # Get temperature, relative humidity, and pressure
    temp = fetch(property='Temp', source='GFS', vert_coord1=level)
    pres = fetch(property='Pres', source='GFS', vert_coord1=None)
    rel_hum = fetch(property='RelHum', source='GFS', vert_coord1=level)
    
    # Package into quantity
    q_temp = units('K') * temp.data
    q_pres = units('Pa') * pres.data
    q_rel_hum = units(None) * rel_hum.data # Dimensionless
    return temp

     

def temp_corr(pressure_arr, temperature_arr):
    """Compute the temperature correction
    """
    pass
    
