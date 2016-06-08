#!/contrib/anaconda/2.3.0/bin/python

# Program converts MDL CSV hourly obs to netCDF
# and stores them into a netCDF file.
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

##### 
#Functions
#####

# Function to create file name from a datetime object
def createFilename(datadir,date):
    yr = str(date.year)
    mt = str(date.month).zfill(2)
    dy = str(date.day).zfill(2)
    hr = str(date.hour).zfill(2)
    datafile = datadir + "/" + yr+mt + "/" + yr+mt+dy+hr
    return datafile

# Function to strip white space from strings
def strip(text):
    try:
        return text.strip()
    except AttributeError:
        return text

def convertToEpoch(value,date):
    datetime = pd.to_datetime(date)
    minutes = int(float(value)) % 100
    if (minutes <= 59 & minutes >= 30):
        seconds_since_epoch = time.mktime(datetime.timetuple()) - minutes*60
    elif (minutes >= 0 & minutes <= 29):
        seconds_since_epoch = time.mktime(datetime.timetuple()) + minutes*60
    return seconds_since_epoch

#####
# Begin main code
#####

# Declare global variables
columns = ['CALL','TYPE','LAT','LON','TIME','TMP','DEW','PRWX1','PRWX2','PRWX3','VIS','WDR',
           'WSP','GST','MSL','ALT','CA1','CH1','CA2','CH2','CA3','CH3','CA4',
           'CH4','CA5','CH5','CA6','CH6','1PCP','3PCP','6PCP','24PP','SUN',
           'MX6','MN6','X24','N24','SND','SNF','SAE','SEE','SAW','SEW','NULL']
var_list_integer = ['TIME','TMP','DEW','VIS','WDR','WSP','GST','MSL','ALT',
                    'CH1','CH2','CH3','CH4','CH5','CH6','1PCP','3PCP','6PCP','24PP',
                    'MX6','MN6','X24','N24','SND']
nc_list = [('Temp','i4'),('Dew','i4'),('Prwx1','i4'),('Prwx2','i4'),('Prwx3','i4'),
           ('Vis','str')]
converters = {'CALL':strip,'TYPE':strip}
obsdata = pd.DataFrame(columns=columns)
datadir = '/scratch3/NCEPDEV/mdl/Jason.Levit/obs'
station_list = []
nc_arrays = []

# Construct a list of dates
start_date = pd.datetime(2016, 1, 1, 0)
end_date = pd.datetime(2016, 1, 1, 6)
daterange = pd.date_range(start_date, end_date, freq='1H')
daterange_epoch = pd.date_range(start_date, end_date, freq='1H').astype(int) // 10**9

# Read in CSV data
for date in daterange:
    print createFilename(datadir,date)
    frame = pd.read_csv(createFilename(datadir,date),sep=":",names=columns,converters=converters,skipfooter=1,skiprows=[0,1],index_col=False)
    frame['TIME'] = frame['TIME'].apply(convertToEpoch,args=(date,))
    obsdata = obsdata.append(frame,ignore_index=True)

# Delete dummy "NULL" column
obsdata.drop(['NULL'],inplace=True,axis=1)

# Change some columns into integer
for var in var_list_integer:
    obsdata[var] = obsdata[var].astype(float)
    obsdata[var] = obsdata[var].astype(int)

# Replace all blank strings in dataframe with "9999"
obsdata = obsdata.replace(r"^\s*$","9999",regex=True)

# Determine unique station list
station_list = list(obsdata['CALL'].unique())

# Create netCDF files
ncfile = Dataset('test.nc',mode='w',format='NETCDF4')
nc_stations = ncfile.createDimension('stations', len(station_list))  
nc_times = ncfile.createDimension('times', len(daterange_epoch))

for nc in nc_list:
   nc_arrays.append(ncfile.createVariable(nc[0],nc[1],('stations','times')))

ncfile.close()

