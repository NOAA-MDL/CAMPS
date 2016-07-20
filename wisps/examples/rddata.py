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
data = []
#data = np.zeros((38,186,1))

start_years=[2014,2015]
end_years=[2015,2016]
numyears = 2

# Create a list of dates
for ny in range(0,numyears):
    start_date = pd.datetime(start_years[ny], 10, 1, 0)
    end_date = pd.datetime(end_years[ny], 3, 31, 23)
    daterange = pd.date_range(start_date, end_date, freq='MS')

# Loop through range of dates, create data file for each month
    for date in daterange:

        nc_dir = '/scratch3/NCEPDEV/mdl/Jason.Levit/wisps/'
        nc_filename = nc_dir + 'gfs_' + date.strftime('%Y%m%d') + ".nc"
        ncfile = Dataset(nc_filename,'r') 

# read the data in variable named 'data'.
        for v in var_list:
            print v, date
            data.append(ncfile.variables[v][0,::4,0])

# close the file.
        ncfile.close()

print len(data)

