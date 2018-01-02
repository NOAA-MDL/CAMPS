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

def temp_corr_setup(mixrat_obj):
    """Compute temperature coreection.
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

     

def temp_corr(pressure_arr, temperature_arr, rel_hum_arr):
    """Compute the temperature correction
    """
    #epsilon = const.ratio_of_dry_and_saturated_gas_constant
    #psat = const.saturated_pressure_at_triple_point
    #saturation_vapor_pressure = calc.saturation_vapor_pressure

    sat_mix_ratio = calc.saturation_mixing_ratio(pressure_arr, temperature_arr)
    mixing_ratio = sat_mix_ratio * rel_hum_arr
    return mixing_ratio
    


    

