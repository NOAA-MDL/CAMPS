#!/usr/bin/env python

# Add a relative path
import sys
import os
import numpy as np
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
import registry.util as cfg
from data_mgmt.Wisps_data import Wisps_data
import data_mgmt.Time as Time
import data_mgmt.reader as reader


# Read in the grib netcdf data

# Read in the station names and their latitude and longitude
