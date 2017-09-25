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

def thickness(thickness_obj):
    """Compute thickness from geopotential heights.
    """
    # First check if object argument actually has two vertical coordinates
    vert_coords = thickness_obj.get_coordinate()
    assert len(vert_coords) == 2
    # Unpack
    height_1, height_2 = vert_coords

    # Get the two geopotential heights
    height_obj1 = fetch(property='GeoHght', source='GFS', vert_coord1=height_1)
    height_obj2 = fetch(property='GeoHght', source='GFS', vert_coord1=height_2)
   
    # Calculate thickness
    data = height_obj2[:] - height_obj1[:]
    thickness_obj.data = data
    return thickness_obj




