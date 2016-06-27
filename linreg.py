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
import statsmodels.formula.api as smf
from forward import forward_selected

def convertToCelsius(value):
    celsius = round((value * 1.8) - 459.67)
    return celsius

def convertToKelvin(value):
    kelvin = round((value + 459.67) * (5.0/9.0))
    return kelvin

# Declare variables
column_list = ['700-500MB THICKNESS','850-700MB THICKNESS','1000-850MB THICKNESS',
               '700MB TEMP','850MB TEMP','925MB TEMP','950MB TEMP','975MB TEMP',
               '1000MB TEMP','700-500M TEMP DIFFERENCE (LAPSE)','850-700M TEMP DIFFERENCE (LAPSE)',
               '1000-850M TEMP DIFFERENCE (LAPSE)','2M TEMP','MAX MAX T 12h','MIN MIN T 12h',
               '12H MAX TEMP','12H MIN TEMP','MEAN RH (1000-500MB)','700-500MB MEAN RELATIVE HUMIDITY',
               '850-700MB MEAN RELATIVE HUMIDITY','1000-850MB MEAN RELATIVE HUMIDITY',
               '700MB DEW POINT TEMP','850MB DEW POINT TEMP','925MB DEW POINT TEMP','950MB DEW POINT TEMP',
               '975MB DEW POINT TEMP','1000MB DEW POINT TEMP','2M DEW POINT TEMP','PRECIP WATER',
               '10M U-WIND','10M V-WIND','10M WIND SPEED','700MB WIND SPEED','850MB WIND SPEED',
               '925MB WIND SPEED','950MB WIND SPEED','975MB WIND SPEED','K-INDEX']

print "WISPS starting. Alpha testing."

# GFS netCDF file name creation
model_dir = '/scratch3/NCEPDEV/mdl/Jason.Levit/wisps/gfs_new/'
model_filename = model_dir + 'u201.gfs00.f030.cl.nc'
model_file = Dataset(model_filename, 'r', format="NETCDF4")

# OBS netCDF file name creation
obs_dir = '/scratch3/NCEPDEV/mdl/Jason.Levit/wisps/obs_new/'
#obs_filename = obs_dir + 'metar_tdmxmn_predictands.nc'
obs_filename = obs_dir + 'u201.gfstemp.tand.cl.nc'
obs_file = Dataset(obs_filename, 'r', format="NETCDF4")

# Create a list of dates
start_years = [2014,2015]
end_years = [2015,2016]
numyears = 2
epoch_range = []
for ny in range(0,numyears):
    start_date = pd.datetime(start_years[ny], 10, 2, 6)
#    end_date = pd.datetime(end_years[ny], 3, 31, 6)
    end_date = pd.datetime(end_years[ny], 4, 1, 6)
    epoch_list = (pd.date_range(start_date, end_date, freq='1D').astype(int) // 10**9)
    for e in epoch_list:
        epoch_range.append(e)

# Read model variable list in numpy array
model_variable_list = np.loadtxt("model_variables.csv",dtype="str")
model_variable_list_rename = np.loadtxt("model_variables_rename.csv",dtype="str")
#df_model = pd.DataFrame(columns=model_variable_list,index=epoch_range)

# Read observation variable list in numpy array
obs_variable_list = np.loadtxt("obs_variables.csv",dtype="str")
#df_obs = pd.DataFrame(columns=obs_variable_list,index=epoch_range)

# Create master data frame, used in regression loop
single = np.array(['_TEMPERATURE'])
df_data = pd.DataFrame(columns=np.concatenate((single,model_variable_list_rename),axis=0),index=epoch_range)

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

# Convert temperature obs to Kelvin
#for e, epoch in enumerate(epoch_range):
#    for n in range(nsta_obs):
#        obs[0,e,n] = convertToKelvin(obs[0,e,n])

model_file.close()
obs_file.close()

print "Begin stepwise linear regression."

# Replace all missing values with numpy NAN
#df_obs.replace(99990000,np.NaN,inplace=True)
#df_model.replace(999900000,np.NaN,inplace=True)
#df_model.replace(99990000,np.NaN,inplace=True)

# Convert some variables to appropriate units
#df_model['_TEMP_Z__2'] = df_model['_TEMP_Z__2'].apply(convertToCelsius)

#for e in epoch_range:
#     print df_obs['_TEMPERATURE'][e], df_model['__700_HEIGHT_700_-500'][e]

# Combine data frames into one
#df_all = pd.merge(df_obs,df_model,left_index=True,right_index=True)
#df_all.rename(columns={'_TEMPERATURE': 'TEMPERATURE', '_TEMP_Z__2': 'TEMP_2M', '__700_HEIGHT_700_-500': 'HEIGHT_75'}, inplace=True)

# Linear regression
#response = "TEMPERATURE"
#selected = "TEMP_2M"
#formula = "{} ~ {} + 1".format(response,selected)
#model = smf.ols(formula,df_all).fit()
#print model.rsquared_adj

#df_new = pd.DataFrame({'Test Obs':[82,37,54]})
#df_all['Intercept'] = np.ones(( len(df_all), ))
#df_new['Intercept'] = np.ones(( len(df_new), ))
#y = df_all._TEMPERATURE
#for v in model_variable_list:
#x = df_all[['_TEMP_Z__2','Intercept']]

# Linear regression using numpy and data frames
for so, station_obs in enumerate(stations_obs):
    for sm, station_model in enumerate(stations_model):
        if (station_obs == station_model):
            nantest = np.isnan(obs[0,:,so])
            if (np.all(nantest) != True):
                df_data['_TEMPERATURE'] = obs[0,:,so]
                for mv, model_var in enumerate(model_variable_list_rename):
                    df_data[model_var] = model[mv,:,sm]
#                   new_col_name = "COL" + str(mv)
#                   df_data.rename(columns={model_var:new_col_name},inplace=True)
                result = forward_selected(df_data,'_TEMPERATURE')
#                print station_obs, result.model.formula, result.rsquared_adj
#                print station_obs, result.model.formula, result.params, result.rsquared_adj
                print station_obs
                print result.summary()
                sys.stdout.flush()

# Linear regression just using numpy alone
#for so, station_obs in enumerate(stations_obs):
#    for sm, station_model in enumerate(stations_model):
#        if (station_obs == station_model):
#            y = obs[0,:,so] 
#            nantest = np.isnan(y)
#            if (np.all(nantest) != True):
#                highest_rsquared = 0.0
#                best_var = ''
#                for v, var in enumerate(model_variable_list):
#                    x = np.column_stack((model[v,:,sm],np.full((nrtm),1)))
#                    result = smf.OLS(y,x,missing='drop').fit()
#                    if (result.rsquared_adj > highest_rsquared):
#                        best_var = var
#                        highest_rsquared = result.rsquared_adj
#                print station_obs, best_var, highest_rsquared

#print model.params
#predictions = model.predict(df_new)
#print predictions

# Create observation data frame
#for so, station_obs in enumerate(stations_obs):
#    if ("CABB    " == station_obs):
#        for e, epoch in enumerate(epoch_range):
#            for to, time_obs in enumerate(times_obs):
#                    if (epoch == time_obs):
#                        df_obs['_TEMPERATURE'][epoch] = obs_file.variables['_TEMPERATURE'][0,to,so]

# Create model data frame
#for sm, station_model in enumerate(stations_model):
#    if ("CABB    " == station_model):
#        for e, epoch in enumerate(epoch_range):
#            for tm, time_model in enumerate(times_model):
#                    if (epoch == time_model+times_model_valid):
#                        for v in model_variable_list:
#                            df_model[v][epoch] = model_file.variables[v][0,tm,sm]




