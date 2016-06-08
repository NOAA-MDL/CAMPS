#!/contrib/anaconda/2.3.0/bin/python

# Program converts CSV hourly obs files to netCDF.
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
    datafile = datadir + "/" + yr+mt + "/" + yr+mt + ".csv"
    return datafile
#####
# Begin main code
#####

# Declare global variables
columns = ['CALL','TYPE','LAT','LON','TIME','TMP','DEW','PRWX1','PRWX2','PRWX3','VIS','WDR',
           'WSP','GST','MSL','ALT','CA1','CH1','CA2','CH2','CA3','CH3','CA4',
           'CH4','CA5','CH5','CA6','CH6','1PCP','3PCP','6PCP','24PCP','SUN',
           'MX6','MN6','X24','N24','SND','SNF','SAE','SEE','SAW','SEW']
nc_list = [('TMP','i4'),('DEW','i4'),('PRWX1','str'),('PRWX2','str'),('PRWX3','str'),
           ('VIS','i4'),('WDR','i4'),('WSP','i4'),('GST','i4'),
           ('MSL','i4'),('ALT','i4'),
           ('CA1','str'),('CH1','i4'),('CA2','str'),('CH2','i4'),
           ('CA3','str'),('CH3','i4'),('CA4','str'),('CH4','i4'),
           ('CA5','str'),('CH5','i4'),('CA6','str'),('CH6','i4'),
           ('1PCP','i4'),('3PCP','i4'),('6PCP','i4'),('24PCP','i4'),
           ('SUN','str'),
           ('MX6','i4'),('MN6','i4'),('X24','i4'),('N24','i4'),('SND','i4'),
           ('SNF','str'),('SAE','str'),('SEE','str'),('SAW','str'),('SEW','str')]
nc_list_nostr = [('TMP','i4'),('DEW','i4'),('VIS','i4'),('WDR','i4'),('WSP','i4'),('GST','i4'),
                 ('MSL','i4'),('ALT','i4'),('1PCP','i4'),('3PCP','i4'),('6PCP','i4'),('24PCP','i4'),
                 ('MX6','i4'),('MN6','i4'),('X24','i4'),('N24','i4'),('SND','i4')]
converters = {'CA6':str,'SUN':str,'SNF':str,'SAE':str,'SEE':str,'SAW':str,'SEW':str}

datadir = '/scratch3/NCEPDEV/mdl/Jason.Levit/obs'
station_list = []
nc_arrays = []

# Construct a list of dates
start_date = pd.datetime(2016, 1, 1, 0)
end_date = pd.datetime(2016, 1, 31, 23)
daterange = pd.date_range(start_date, end_date, freq='1M')
daterange_epoch = pd.date_range(start_date, end_date, freq='1H').astype(int) // 10**9

# Read in CSV data
for date in daterange:
    print createFilename(datadir,date)
    obsdata = pd.read_csv(createFilename(datadir,date),sep=",",converters=converters,names=columns,skipfooter=1,skiprows=[0],index_col=False)

# Determine unique station list
station_list = list(obsdata['CALL'].unique())

# Create netCDF files
ncfile = Dataset('201601.nc',mode='w',format='NETCDF4')
nc_stations = ncfile.createDimension('stations', len(station_list))  
nc_times = ncfile.createDimension('times', len(daterange_epoch))

# Create netCDF variables
for nc in nc_list_nostr:
   nc_arrays.append(ncfile.createVariable(nc[0],nc[1],('stations','times'),zlib=True))

# Loop through all times and stations, write into variables
for s, stn in enumerate(station_list):
    start = time.time()
    print stn
    sys.stdout.flush()
    query_stn = obsdata.query('CALL == @stn') 
#    query_stn = obsdata[(obsdata.CALL == stn)]
    for e, epoch in enumerate(daterange_epoch):
#        query_time = query_stn.query('(@epoch -900) <= TIME >= (@epoch + 900)')
#        query_time = query_stn[(query_stn.TIME >= epoch-900) & (query_stn.TIME <= epoch+900)]
        query_time = query_stn[(query_stn.TIME == epoch)]
        if (query_time.shape[0] == 1):
            for v, var in enumerate(nc_list_nostr):
                nc_arrays[v][s,e] = query_time[var[0]].item()
        elif (query_time.shape[0] == 0):
            for v, var in enumerate(nc_list_nostr):
                nc_arrays[v][s,e] = 9999
        elif (query_time.shape[0] > 1):
            for v, var in enumerate(nc_list_nostr):
                nc_arrays[v][s,e] = query_time[var[0]].iloc[0]
    end = time.time()
    print(end - start)

       
#        for row in query_stn.itertuples():
#            if ((row[5] >= (time - 900)) & (row[5] <= (time + 900))):
#                for v, var in enumerate(nc_list_nostr):
#                    nc_arrays[v][s,t] = row[v+2]

#    print stn
#    sys.stdout.flush()
#    query_stn = obsdata.query('CALL == @stn') 
#    for t, time in enumerate(daterange_epoch): 
#        for row in query_stn.itertuples():
#            if (row[n query_stn.itertuples():
#            if (row['TIME'] >= (time - 900) & row['TIME'] <= (time + 900)):
#                print row


#        query_time = query_stn.where('(TIME >= @time - 900) & (TIME <= @time + 900)')
#        query_time = query_stn.where[query_stn.TIME >= (time - 900) & query_stn.TIME <= (time + 900)]
#        print query_time
#        if (query_time.shape[0] == 1):
#            for v, var in enumerate(nc_list_nostr):
#                nc_arrays[v][s,t] = query_time[var[0]].item()
#        elif (query_time.shape[0] == 0):
#            for v, var in enumerate(nc_list_nostr):
#                nc_arrays[v][s,t] = 9999
#        elif (query_time.shape[0] > 1):
#            for v, var in enumerate(nc_list_nostr):
#                nc_arrays[v][s,t] = query_time[var[0]].iloc[0]

ncfile.close()
