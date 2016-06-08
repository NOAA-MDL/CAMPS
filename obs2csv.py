#!/contrib/anaconda/2.3.0/bin/python

# Program converts MDL CSV hourly obs to a cleaned
# CSV file, ready for merging and eventual conversion
# to netCDF.
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

# Function to create input file name from a datetime object
def createHREFilename(datadir,date):
    yr = str(date.year)
    mt = str(date.month).zfill(2)
    dy = str(date.day).zfill(2)
    hr = str(date.hour).zfill(2)
    datafile = datadir + "/" + yr+mt + "/" + yr+mt+dy+hr
    return datafile

# Function to create output file name from a datetime object
def createCSVFilename(datadir,date):
    yr = str(date.year)
    mt = str(date.month).zfill(2)
    dy = str(date.day).zfill(2)
    hr = str(date.hour).zfill(2)
    datafile = datadir + "/" + yr+mt + "/" + yr+mt+dy+hr + ".csv"
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
           'CH4','CA5','CH5','CA6','CH6','1PCP','3PCP','6PCP','24PCP','SUN',
           'MX6','MN6','X24','N24','SND','SNF','SAE','SEE','SAW','SEW','NULL']
var_list_integer = ['TIME','TMP','DEW','VIS','WDR','WSP','GST','MSL','ALT',
                    'CH1','CH2','CH3','CH4','CH5','CH6','1PCP','3PCP','6PCP','24PCP',
                    'MX6','MN6','X24','N24','SND']
converters = {'CALL':strip,'TYPE':strip,'CA1':str,'CA2':str,'CA3':str,'CA4':str,'CA5':str,'CA6':str}
obsdata = pd.DataFrame(columns=columns)
datadir = '/scratch3/NCEPDEV/mdl/Jason.Levit/obs'

# Construct a list of dates
start_date = pd.datetime(2016, 1, 1, 0)
end_date = pd.datetime(2016, 1, 31, 23)
daterange = pd.date_range(start_date, end_date, freq='1H')
daterange_epoch = pd.date_range(start_date, end_date, freq='1H').astype(int) // 10**9

# Read in CSV data
for date in daterange:
    print createHREFilename(datadir,date)
    frame = pd.read_csv(createHREFilename(datadir,date),sep=":",names=columns,converters=converters,skipfooter=1,skiprows=[0,1],index_col=False)
    frame['TIME'] = frame['TIME'].apply(convertToEpoch,args=(date,))

# Delete dummy "NULL" column
    frame.drop(['NULL'],inplace=True,axis=1)

# Replace all blank strings in dataframe with "9999"
    frame = frame.replace(r"^\s*$","9999",regex=True)

# Change some columns into integer
    for var in var_list_integer:
        frame[var] = frame[var].astype(float)
        frame[var] = frame[var].astype(int)

# Write out new, cleaned, CSV file
    frame.to_csv(createCSVFilename(datadir,date),sep=",",index=False)
