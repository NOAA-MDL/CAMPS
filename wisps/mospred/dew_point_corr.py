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

def dewpoint_corr_setup(dewpt_obj):
    """Compute gridded dew point 
    temperature correction using pressure, mixing ratio,
    or specific humidity on an
    isobaric, constant height, or a sigma surface.
    """
    level = dewpt_obj.get_coordinate()
    if level != 2 or level is not None:
        raise ValueError("level is not surface or 2m")

    return dewpt_obj



