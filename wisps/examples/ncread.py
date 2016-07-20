# Program reads netCDF files and converts to monthly groups.
# Jason Levit, MDL, April 2016

# Declare imports
import csv
import pandas as pd
import numpy as np
import sys
import time
from datetime import datetime, date, timedelta
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

# Read in station list into numpy array
station_list = np.loadtxt("stations.csv",dtype="str")

# Read variable list in numpy array
variable_list = np.loadtxt("variables.csv",dtype="str")

# Create a list of dates
start_date = pd.datetime(2015, 10, 1, 0)
end_date = pd.datetime(2016, 3, 31, 23)
daterange = pd.date_range(start_date, end_date, freq='MS')

# Begin netCDF file creation
nc_dir = '/scratch3/NCEPDEV/mdl/Jason.Levit/wisps/gfsmos_temp_test/u201/'
nc_filename = nc_dir + 'u201.gfs00.f006.cl.nc'
ncfile = Dataset(nc_filename, 'r', format="NETCDF4")

data = np.ndarray((38,365,3001),dtype="i4")

# read the data in variable named 'data'.
for v, var in enumerate(variable_list):
    data[v,:,:] = ncfile[var][:]

print data[1,40,450]

# close the file.
ncfile.close()


