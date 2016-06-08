#!/contrib/anaconda/2.3.0/bin/python

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


# Function to create 3D array of random integers
def createRandomArray(randwx):
    for i, s in enumerate(station_list):
        for j, t in enumerate(range(1,daysinmonth+1)):
            for k, v in enumerate(range(0,numvars)):
                randwx[i,j,k] = np.random.random_integers(-1000,1000)
    return randwx 

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

numsta = len(station_list)
daysinmonth = 31
numvars = 38

hours = []

randwx = np.ndarray(shape=(len(station_list),daysinmonth,numvars),dtype="i2")

#comp_type = np.dtype([('Station', np.str_, 6), ('Value', 'i2')])
#data = np.ndarray(shape=(3029),dtype=comp_type)
#for i, s in enumerate(station_list):
#    test = np.array((s,random.randint(-1000,1000)),dtype=comp_type)
#    data[i] = test


# "Pretend" to interpolate data for each station and variable
#for s in station_list:
#    for d in range(1,daysinmonth+1):
#        for v in var_list:
#            data[s][d][v]=random.randint(-1000,1000)

#for i, s in enumerate(station_list):
#   for j, t in enumerate(range(1,daysinmonth+1)):
#       for k, v in enumerate(range(0,numvars)):
#           data[i,j,k] = (str(s),t,random.randint(-1000,1000))

# Create a list of dates
start_date = pd.datetime(2015, 10, 1, 0)
end_date = pd.datetime(2016, 3, 31, 23)
daterange = pd.date_range(start_date, end_date, freq='MS')

date = daterange[0]

# Compute a list of projection hours
for h in range(6,195,3):
    hours.append(str(h).zfill(3))
for h in range(198,390,6):
    hours.append(str(h).zfill(3))

# Begin HDF5 file creation
hd_dir = '/scratch3/NCEPDEV/mdl/Jason.Levit/wisps/'
hd_filename = hd_dir + 'gfs_' + date.strftime('%Y%m%d') + ".h5"

with h5py.File(hd_filename, 'w') as hf:
    hf.attrs["dimensions"] = ([("stations",3029),("dates",31),("variables",38)])
    hf.attrs["dimension1"] = 3029
    hf.attrs["dimension2"] = 31
    hf.attrs["dimension3"] = 38
    hf.attrs["stations_xdim"] = station_list
    hf.attrs["valid_dates_ydim"] = "000"
    hf.attrs["variables_zdim"] = var_list
    for cycle in range(0,24,6):
        for hr in hours:
            print cycle, hr
            group_name = "GFS/" + str(cycle).zfill(2) + "Z/" + "/" + hr
            hf.create_dataset(group_name, data=createRandomArray(randwx), dtype="i4", compression="gzip", shuffle="True")

#with h5py.File(hd_filename, 'w') as hf:
#    for cycle in range(0,24,6):
#        for hour in range (0,195,3):
#            for day in range (1,32):
#                print cycle, hour, day
#                for var in var_list:
#                    group_name = "GFS/" + str(cycle).zfill(2) + "Z/" + str(hour).zfill(3) + "/" + str(day) + "/" + var
#                    hf.create_dataset(group_name, data=data, dtype=comp_type, compression="gzip", compression_opts=4)

sys.exit()

#########

# Create a list of dates
start_date = pd.datetime(2015, 10, 1, 0)
end_date = pd.datetime(2016, 3, 31, 23)
daterange = pd.date_range(start_date, end_date, freq='MS')

# Loop through range of dates, create data file for each month
#for date in daterange:

date = daterange[0]

# Begin HDF5 file creation
hd_dir = '/scratch3/NCEPDEV/mdl/Jason.Levit/wisps/'
hd_filename = hd_dir + 'gfs_' + date.strftime('%Y%m%d') + ".h5"
#f = h5py.File(hd_filename, "w")

rand_data = np.random.randint(-1000,high=1001,size=(3029,28))

with h5py.File(hd_filename, 'w') as hf:
    for cycle in range(0,24,6):
        for station in station_list:
            for hour in range (6,243,3):  
                for var in var_list:
                    group_name = "GFS/" + str(cycle).zfill(2) + "/"  
            print group_name
            hf.create_dataset(group_name, data=rand_data, dtype="i4", compression="gzip", compression_opts=4)

# Create a list of 6H cycles in current month
start_hour = date
end_hour = datetime(date.year,date.month,date.daysinmonth,23)
hourrange = pd.date_range(start_hour, end_hour, freq='6H')

# Create a list of days in current month
start_day = date
end_day = datetime(date.year,date.month,date.daysinmonth,23)
dayrange = pd.date_range(start_hour, end_hour, freq='1D')

cycle=0

for day in dayrange:
    for fhr in range (0,195,3):
        subgroup_name = "/" + str(cycle).zfill(2) + "/" + str(fhr).zfill(3) + "/" + day.strftime('%Y%m%d')

#f["Dataset1"] = 1.0

#    var_string = '00Z/000/' + date.strftime('%Y%m%d')+ '/' + s + "/" + v
#    master_var_list.append((var_string, 'i1'))

#    comp_type = np.dtype(master_var_list)
#    dataset = f.create_dataset("GFS",(3000,), comp_type)

# rtime = 124
# vtime = 81

# Loop through variable name list, create HDF5 variables
#    for count, var in enumerate(var_list):
#        dset = f.create_dataset(var, (81,date.daysinmonth*4,3029), dtype='i1')

#        hd_list.append(rootgrp.createVariable(var,'i1',('vtime','rtime','stn'),zlib=True))

#    for v in range(0,81):
#       vtimes[v] = v*10800

#    start_hour = date
#    end_hour = datetime(date.year,date.month,date.daysinmonth,23)
#    hourrange = pd.date_range(start_hour, end_hour, freq='6H')

#    for count, h in enumerate(hourrange):
#        rtimes[count] = time.mktime(h.timetuple())

# Create a bunch of random data and store in each HDF5 variable
#    for list in range(0,len(nc_list)):
#        random_data = np.aandom.randint(-1000,high=1001,size=(81,date.daysinmonth*4,3029))
#        nc_list[list][:] = random_data
    
# Close netCDF file
#    rootgrp.close()


