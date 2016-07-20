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

#comp_type = np.dtype([("Station ID", np.str_, 6),
#                      ("Date", "i8"),

comp_type = np.dtype([("700-500MB THICKNESS", "i2"),
                      ("850-700MB THICKNESS", "i2"),
                      ("1000-850MB THICKNESS", "i2"),
                      ("700MB TEMP", "i2"),
                      ("850MB TEMP", "i2"),
                      ("925MB TEMP", "i2"),
                      ("950MB TEMP", "i2"),
                      ("975MB TEMP", "i2"),
                      ("700-500M TEMP DIFFERENCE (LAPSE)", "i2"),
                      ("850-700M TEMP DIFFERENCE (LAPSE)", "i2"),
                      ("1000-850M TEMP DIFFERENCE (LAPSE)", "i2"),
                      ("2M TEMP", "i2"),
                      ("MAX MAX T 12h", "i2"),
                      ("MIN MIN T 12h", "i2"),
                      ("12H MAX TEMP", "i2"),
                      ("12H MIN TEMP", "i2"),
                      ("MEAN RH (1000-500MB)", "i2"),
                      ("700-500MB MEAN RELATIVE HUMIDITY", "i2"),
                      ("850-700MB MEAN RELATIVE HUMIDITY", "i2"),
                      ("1000-850MB MEAN RELATIVE HUMIDITY", "i2"),
                      ("700MB DEW POINT TEMP", "i2"),
                      ("850MB DEW POINT TEMP", "i2"),
                      ("925MB DEW POINT TEMP", "i2"),
                      ("950MB DEW POINT TEMP", "i2"),
                      ("975MB DEW POINT TEMP", "i2"),
                      ("1000MB DEW POINT TEMP", "i2"),
                      ("2M DEW POINT TEMP", "i2"),
                      ("PRECIP WATER", "i2"),
                      ("10M U-WIND", "i2"),
                      ("10M V-WIND", "i2"),
                      ("10M WIND SPEED", "i2"),
                      ("700MB WIND SPEED", "i2"),
                      ("850MB WIND SPEED", "i2"),
                      ("925MB WIND SPEED", "i2"),
                      ("950MB WIND SPEED", "i2"),
                      ("875MB WIND SPEED", "i2"),
                      ("K-INDEX", "i2")])

# Read in station list into numpy array
station_list = np.loadtxt("stations.csv",dtype="str")

numsta = len(station_list)

# Create a list of dates
start_date = pd.datetime(2015, 10, 1, 0)
end_date = pd.datetime(2016, 3, 31, 23)
daterange = pd.date_range(start_date, end_date, freq='MS')

date = daterange[0]

# Begin HDF5 file creation
hd_dir = '/scratch3/NCEPDEV/mdl/Jason.Levit/wisps/'
hd_filename = hd_dir + 'gfs_' + date.strftime('%Y%m%d') + ".h5"
store = pd.HDFStore(hd_filename,"w")

for cycle in range(0,6,6):
    for hour in range (0,6,3):
        wp = pd.Panel(np.random.randn(numsta, 31, 38), items=station_list,
             major_axis=pd.date_range('10/1/2015', periods=31),
             minor_axis=var_list,
             dtype="i2")
        group_name = "GFS/C" + str(cycle).zfill(2) + "/F" + str(hour).zfill(3)
        print group_name
        store.append(group_name, wp)

print store
       
# Create a list of 6H cycles in current month
start_hour = date
end_hour = datetime(date.year,date.month,date.daysinmonth,23)
hourrange = pd.date_range(start_hour, end_hour, freq='6H')

# Create a list of days in current month
start_day = date
end_day = datetime(date.year,date.month,date.daysinmonth,23)
dayrange = pd.date_range(start_hour, end_hour, freq='1D')

