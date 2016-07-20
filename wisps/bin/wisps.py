#! /usr/bin/env python

'''
Program reads MDL netCDF files and runs a stepwise linear regression.
Jason Levit, CIRA/MDL, May 2016
'''

# Declare imports
import csv
import numpy as np
import pandas as pd
import sys
import time
from datetime import datetime, date, timedelta
import calendar
from netCDF4 import Dataset 
from math import stepregress

# Declare mathematical functions
def convertToCelsius(value):
    celsius = round((value * 1.8) - 459.67)
    return celsius

def convertToKelvin(value):
    kelvin = round((value + 459.67) * (5.0/9.0))
    return kelvin

print "WISPS starting. Alpha testing."

# GFS netCDF file name creation
model_dir = '/scratch3/NCEPDEV/mdl/Jason.Levit/wisps/gfs_new/'
model_filename = model_dir + 'u201.gfs00.f030.cl.nc'
model_file = Dataset(model_filename, 'r', format="NETCDF4")

# OBS netCDF file name creation
obs_dir = '/scratch3/NCEPDEV/mdl/Jason.Levit/wisps/obs_new/'
obs_filename = obs_dir + 'u201.gfstemp.tand.cl.nc'
obs_file = Dataset(obs_filename, 'r', format="NETCDF4")

# Create a list of dates
start_years = [2014,2015]
end_years = [2015,2016]
numyears = 2
epoch_range = []
for ny in range(0,numyears):
    start_date = pd.datetime(start_years[ny], 10, 2, 6)
    end_date = pd.datetime(end_years[ny], 4, 1, 6)
    epoch_list = (pd.date_range(start_date, end_date, freq='1D').astype(int) // 10**9)
    for e in epoch_list:
        epoch_range.append(e)

# Read model variable list in numpy array
model_variable_list = np.loadtxt("model_variables.csv",dtype="str")

# Read observation variable list in numpy array
obs_variable_list = np.loadtxt("obs_variables.csv",dtype="str")

# Read station and time list from obs and model
stations_obs = obs_file.variables['station'][:]
stations_model = model_file.variables['station'][:]
times_obs = obs_file.variables['rtime'][:].astype(int)
times_model = model_file.variables['rtime'][:].astype(int)
times_model_valid =  model_file.variables['vtime'][:].astype(int)
times_model_add = np.add(times_model,times_model_valid)

stations_obs = map(''.join, stations_obs)
stations_model = map(''.join, stations_model)

# Read in observation data into numpy array
print "Reading observation data."
nsta_obs = int(len(obs_file.dimensions['nsta']))
nrtm_obs = int(len(obs_file.dimensions['rtime']))
nvar_obs = int(len(obs_variable_list))
nrtm = len(epoch_range)
print nsta_obs, nrtm, nvar_obs
obs = np.empty([nvar_obs,nrtm,nsta_obs])
for v, var in enumerate(obs_variable_list):
    for e, epoch in enumerate(epoch_range):
        for t, time in enumerate(times_obs):
            if (epoch == time):
                obs[v,e,:] = obs_file.variables[var][0,t,:]

# Read in model data into numpy array
print "Reading model data."
nsta_model = int(len(model_file.dimensions['nsta']))
nrtm_model = int(len(model_file.dimensions['rtime']))
nvar_model = int(len(model_variable_list))
nrtm = len(epoch_range)
print nsta_model, nrtm, nvar_model
model = np.empty([nvar_model,nrtm,nsta_model])
for v, var in enumerate(model_variable_list):
    for e, epoch in enumerate(epoch_range):
        for t, time in enumerate(times_model_add):
            if (epoch == time):
                model[v,e,:] = model_file.variables[var][0,t,:]

# Replace all missing values with numpy NAN
obs[obs == 9999.0] = np.NaN
model[model == 9999.0] = np.NaN

model_file.close()
obs_file.close()

# Quality control data; look for all NaNs or less than 200 observations

print "Begin stepwise linear regression."

# Stepwise linear regression using numpy and smf.OLS
for so, station_obs in enumerate(stations_obs):
    for sm, station_model in enumerate(stations_model):
        if (station_obs == station_model):
            nantest = np.isnan(obs[0,:,so])
            if (np.all(nantest) != True):
                result, predictors = stepregress(model[:,:,sm],y = obs[0,:,so])
            print station_obs, result.rsquared_adj
            for pd, predict in enumerate(predictors):
                print result.params[pd],model_variable_list[predict]
            print result.params[-1], "INTERCEPT"

