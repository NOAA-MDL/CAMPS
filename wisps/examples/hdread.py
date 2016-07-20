# Program creates fake, interpolated model data from a list of observation sites
# and stores them into a HDF5 file.
# Jason Levit, MDL, May 2016

# Declare imports
import csv
import pandas as pd
import numpy as np
import sys
import time
from datetime import datetime, date, timedelta
from pandas.tseries.offsets import *
import calendar
import h5py
import random

# Declare global variables
var_list = ['700-500MB THICKNESS','850-700MB THICKNESS','1000-850MB THICKNESS',
            '700MB TEMP','850MB TEMP','925MB TEMP','950MB TEMP','975MB TEMP',
            '1000MB TEMP','700-500M TEMP DIFFERENCE (LAPSE)','850-700M TEMP DIFFERENCE (LAPSE)',
            '1000-850M TEMP DIFFERENCE (LAPSE)','2M TEMP','MAX MAX T 12h','MIN MIN T 12h',
            '12H MAX TEMP','12H MIN TEMP','MEAN RH (1000-500MB)','700-500MB MEAN RELATIVE HUMIDITY',
            '850-700MB MEAN RELATIVE HUMIDITY','1000-850MB MEAN RELATIVE HUMIDITY',
            '700MB DEW POINT TEMP','850MB DEW POINT TEMP','925MB DEW POINT TEMP','950MB DEW POINT TEMP',
            '975MB DEW POINT TEMP','1000MB DEW POINT TEMP','2M DEW POINT TEMP','PRECIP WATER',
            '10M U-WIND','10M V-WIND','10M WIND SPEED','700MB WIND SPEED','850MB WIND SPEED',
            '925MB WIND SPEED','950MB WIND SPEED','975MB WIND SPEED','K-INDEX']

hd_filename = "/scratch3/NCEPDEV/mdl/Jason.Levit/wisps/gfs_20151001.h5"

rdata = np.ndarray((3029,31,38,4),dtype="i2")

with h5py.File(hd_filename,"r") as f:
    for c, cycle in enumerate(range(0,24,6)):
        group_name = "/GFS/" + str(cycle).zfill(2) + "Z/000"
        dset = f[group_name]
        rdata[:,:,:,c] = dset[...]

print rdata[0,0,0,:]
