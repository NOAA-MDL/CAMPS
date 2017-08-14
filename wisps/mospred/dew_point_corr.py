import os
import sys
import re
import pdb
relative_path = os.path.abspath(
    os.path.dirname(os.path.realpath(__file__)) + "/..")
sys.path.insert(0, relative_path)
from data_mgmt.fetch import *

#import metpy.constants as const
import data_mgmt.constants as const
import metpy.calc as calc
from metpy.units import units

def dewpoint_corr_setup(dewpt_obj):
    """Compute gridded dew point 
    temperature correction using pressure, mixing ratio,
    or specific humidity on an
    isobaric, constant height, or a sigma surface.
    """
    level = dewpt_obj.get_coordinate()
    if level != 2 or level is not None:
        raise ValueError("level is not surface or 2m")

    temp = fetch(property='Temp', source='GFS', vert_coord1=level)
    rel_hum = fetch(property='RelHum', source='GFS', vert_coord1=level)
    
    # Package into quantity
    q_temp = units('K') * temp.data
    q_rel_hum = units(None) * rel_hum.data # Dimensionless

    data = calc.dewpoint_rh(q_temp, q_rel_hum)

    dewpt_obj.data = data
    return dewpt_obj



