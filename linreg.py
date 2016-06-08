#!/contrib/anaconda/2.3.0/bin/python

# Program reads MDL netCDF files and runs a linear regression.
# Jason Levit, MDL, May 2016

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
model_variable_list = np.loadtxt("variables.csv",dtype="str")

# Create a list of dates
start_date = pd.datetime(2015, 10, 1, 0)
end_date = pd.datetime(2016, 3, 31, 23)
daterange = pd.date_range(start_date, end_date, freq='MS')

# GFS netCDF file creation
model_dir = '/scratch3/NCEPDEV/mdl/Jason.Levit/wisps/gfs/'
model_filename = model_dir + 'u201.gfs00.f006.cl.nc'
model_file = Dataset(model_filename, 'r', format="NETCDF4")

# OBS netCDF file creation
obs_dir = '/scratch3/NCEPDEV/mdl/Jason.Levit/wisps/obs/'
obs_files=[(obs_dir + '201311.nc'),(obs_dir + '201312.nc'),
           (obs_dir + '201401.nc'),(obs_dir + '201402.nc'),
           (obs_dir + '201403.nc'),(obs_dir + '201411.nc'),
           (obs_dir + '201412.nc'),(obs_dir + '201501.nc'),
           (obs_dir + '201502.nc'),(obs_dir + '201503.nc'),
           (obs_dir + '201510.nc'),(obs_dir + '201511.nc')]

# read the GFS model data
model_data = np.ndarray((38,365,3001),dtype="i4")
for v, var in enumerate(model_variable_list):
    model_data[v,:,:] = model_file[var][:]

stations=[]
# read the observation data
for obs in obs_files:
    obs_file = Dataset(obs, 'r', format="NETCDF4")
    stations.append(obs_file.variables['station'][:].tolist())

s = pd.Series(stations)

print s

print s.unique()

sys.exit()

index = obs_file.variables['rtime'][:]
stations = obs_file.variables['station'][:]

columns = []
for s in stations:
    columns.append(''.join(s[0:8]))

data = obs_file.variables['_TEMPERATURE'][0,:,:]

df = pd.DataFrame(data,index=index,columns=columns)

#obs_data = np.ndarray((vtime,rtime,nsta),dtype="i4")
    
# read in the observation data
#for obs in obs_files:
#    obs_file = Dataset(obs, 'r', format="NETCDF4")
#    obs_data.append(obs_file['_TEMPERATURE'][:])

# close the file.
model_file.close()


