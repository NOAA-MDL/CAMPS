import os
import sys
import re
import pdb
import metpy
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


def dewpoint_setup(time, dewpt_obj):
    """Compute gridded dew point 
    temperature using pressure, mixing ratio,
    or specific humidity on an
    isobaric, constant height, or a sigma surface.
    """
    level = dewpt_obj.get_coordinate()
    if level != 2 or level is not None:
        raise ValueError("level is not surface or 2m")

    temp = fetch(property='Temp', source='GFS', vert_coord1=level)
    rel_hum = fetch(property='RelHum', source='GFS', vert_coord1=level)
    
    # Package into Pint quantity
    q_temp = units('K') * temp.data
    q_rel_hum = units(None) * rel_hum.data # Dimensionless

    data = metpy.calc.dewpoint_rh(q_temp, q_rel_hum)

    dewpt_obj.data = data
    return dewpt_obj



def mixing_ratio_setup(time, pred):
    """Compute gridded mixing ratio using 
    pressure, temperature, and relative humidity (%) 
    on an isobaric, a constant height, or a sigma surface.
    """
    # Only will work if surface or 2m elevation
    level = mixrat_obj.get_coordinate()
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

    data = mixing_ratio(q_temp, q_pres, q_relum)
    mixrat_obj.data = data
    return mixrat_obj



def mixing_ratio(pressure_arr, temperature_arr, rel_hum_arr):
    """Compute the mixing ratio
    """
    #epsilon = const.ratio_of_dry_and_saturated_gas_constant
    #psat = const.saturated_pressure_at_triple_point
    #saturation_vapor_pressure = calc.saturation_vapor_pressure

    sat_mix_ratio = calc.saturation_mixing_ratio(pressure_arr, temperature_arr)
    mixing_ratio = sat_mix_ratio * rel_hum_arr
    return mixing_ratio
    
