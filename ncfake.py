#!/contrib/anaconda/2.3.0/bin/python

# Program creates fake, interpolated model data from a list of observation sites
# and stores them into a netCDF file.
# Jason Levit, MDL, April 2016

# Declare imports
import csv
import pandas as pd
import numpy as np
import sys
import time
from datetime import datetime, date, timedelta
from pandas.tseries.offsets import *
import calendar
from netCDF4 import Dataset 

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

nc_list = []

# Read in station list into numpy array
station_list = np.loadtxt("stations.csv",dtype="str")

# Create a list of dates
start_date = pd.datetime(2015, 10, 1, 0)
end_date = pd.datetime(2016, 3, 31, 23)
daterange = pd.date_range(start_date, end_date, freq='MS')

# Loop through range of dates, create data file for each month
for date in daterange:

# Begin netCDF file creation
    nc_dir = '/scratch3/NCEPDEV/mdl/Jason.Levit/wisps/'
    nc_filename = nc_dir + 'gfs_' + date.strftime('%Y%m%d') + ".nc"
    rootgrp = Dataset(nc_filename, 'w', format="NETCDF4")

#level = rootgrp.createDimension('level', None)
#lat = rootgrp.createDimension('lat', None)
#lon = rootgrp.createDimension('lon', None)
    rtime = rootgrp.createDimension('rtime', None)
    vtime = rootgrp.createDimension('vtime', None)
    stn = rootgrp.createDimension('stn', 3029)

    rtimes = rootgrp.createVariable('rtimes','i4',('rtime'),zlib=True)
    vtimes = rootgrp.createVariable('vimes','i4',('vtime'),zlib=True)
    stations = rootgrp.createVariable('stn',str,('stn'),zlib=True)

    stations[:] = station_list

# Loop through variable name list, create a list of netCDF variables
    for var in var_list:
        nc_list.append(rootgrp.createVariable(var,'i2',('vtime','rtime','stn'),zlib=True))

    for v in range(0,81):
       vtimes[v] = v*10800

    start_hour = date
    end_hour = datetime(date.year,date.month,date.daysinmonth,23)
    hourrange = pd.date_range(start_hour, end_hour, freq='6H')

    for count, h in enumerate(hourrange):
        rtimes[count] = time.mktime(h.timetuple())

# Create a bunch of random data and store in each netCDF variable
    for list in range(0,len(nc_list)):
        random_data = np.random.randint(-1000,high=1001,size=(81,date.daysinmonth*4,3029))
        nc_list[list][:] = random_data
    
# Close netCDF file
    rootgrp.close()


