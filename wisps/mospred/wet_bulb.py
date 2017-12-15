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

def wet_bulb_setup(mixrat_obj):
    """Compute gridded mixing ratio using 
    pressure, temperature, and relative humidity (%) 
    on an isobaric, a constant height, or a sigma surface.
    """
    level = mixrat_obj.get_coordinate()
    if level != 2 or level is not None:
        raise ValueError("level is not surface or 2m")
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



def wet_bulb(pressure_arr, temperature_arr, rel_hum_arr):
    """Compute the mixing ratio
    """
    pass
    


