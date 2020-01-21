#!/usr/bin/env python
import os
import sys
from netCDF4 import Dataset
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import OrderedDict
import pdb

file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = '/..'
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0,path)

from core.reader import read
from registry.db.update_db import update
import registry.util as cfg
from mospred import read_pred as read_pred
from mospred import parse_pred as parse_pred
from core import Time as Time
from core.fetch import *
from mospred import create

def stations(station_let):
	"""
	merges station letters into single list of station names
	"""
	stat = ['']*np.size(station_let,0)
	for i in range(len(stat)):
		for j in range(4):
			if station_let[i][j] is not np.ma.masked:
				stat[i]+=station_let[i][j]
	return stat

def gmt(time):
	"""
	converts time to gmt, appends to list
	"""
        gmt = [0]*time.size
        for i in range(time.size):
                gmt[i]=datetime.utcfromtimestamp(time[i]).strftime('%Y-%m-%d %H:%M:%S')
        return gmt

def miss_station(all_stations,stations):
	"""
	finds stations that don't have predictand data and appends them to a list
	"""
	diff = len(all_stations)-len(stations)
        k=0
        i=0
        miss_stations = ['']*diff
        a = all_stations[:]
        a.sort()
        s = stations[:]
        s.sort()
        while i < len(stations):
                while a[i] != s[i]:
                        miss_stations[k]=a[i]
                        del a[i]
                        k+=1
                i+=1
	return miss_stations

def dataframe():
	"""
	builds and saves dataframe to be used for graphs
        """
	#allows function to access station, gmt, and miss_station functions
        global stations
	global gmt
	global miss_station
	
	#read predictor file
	control = cfg.read_yaml('../registry/graphs.yaml')
	pred_ctrl = cfg.read_yaml(cfg.get_config_path(control.pred_file))
	predd_ctrl = cfg.read_yaml(cfg.get_config_path(control.predd_file))

	#get file paths and update database
	predictor_file_path = control.predictor_file_path
	predictand_file_path = control.predictand_file_path
	pred_file_id = update(predictor_file_path)
	predd_file_id = update(predictand_file_path)
	
	#store lead time and date range
	lead_time = control.lead_time
	date_range = control.date_range

	#get info for fetch many dates
	start,end,stride = read_pred.parse_range(date_range)
	fcst_ref_time = control.date_range[0].split('-')[0][-2:]
	
	#initialize list of predictors
	pred_list = pred_ctrl.predictors
	predictor = []

	#loops through predictors to build camps data objects
	for entry_dict in pred_list:
		#formats metadata
		pred = create.preprocess_entries(entry_dict, fcst_ref_time)
		
		#adds info to metadata that's not currently being stored
		pred.search_metadata['reserved2'] = lead_time*3600
                pred.search_metadata['file_id'] = pred_file_id
		pred.search_metadata['reserved1'] = 'vector'

		#build camps data objects for each day
		variable = fetch_many_dates(predictor_file_path,start,end,stride,pred.search_metadata)
		
		#appends all data to single camps object
		if variable[0] is not None:
			var = variable[0]
			arrs = []
			for i in range(len(variable)):
				arrs.append(variable[i].data)
			var.data = np.stack(arrs)
			predictor.append(var)

	#initializes list of predictands
	predd_list = predd_ctrl.predictands
        predictand = []
	
	#loops through predictands to build camps data objects
        for entry_dict in predd_list:
		#formats metadata
        	vertical_coordinate = entry_dict.pop('Vertical_Coordinate')
		entry_dict['file_id'] = predd_file_id

		#build camps objects for each day
                variable = fetch_many_dates(predictand_file_path,start, end, stride, entry_dict)

		#append all data to single camps object
                var = variable[0]
                arrs = []
                for i in range(len(variable)):
                        arrs.append(variable[i].data)
                try:
			var.data = np.stack(arrs)
			predictand.append(var)
		except:
			print("Can't read " + variable.name)

	#getting predictor station and time data
	predr = Dataset(predictor_file_path[0])
	predr_stat = predr.variables['station'][:]
	if lead_time == 3:
		predr_time = predr.variables['OM__phenomenonTimeInstant'][:]
	elif lead_time == 6:
		predr_time = predr.variables['OM__phenomenonTimeInstant1'][:]
	elif lead_time == 12:
		predr_time = predr.variables['OM__phenomenonTimeInstant2'][:]
	predr.close()

	#reformatting predictor station and time data
	predr_stations = stations(predr_stat)
	predr_gmt = gmt(predr_time)
	
	#getting predictand station and time data
	predd = Dataset(predictand_file_path[0])
	predd_stat = predd.variables['station'][:]
	predd_time = predd.variables['OM__resultTime'][:]
	predd.close()
	
	#reformatting predictand station and time data
	predd_stations = stations(predd_stat)
	predd_gmt = gmt(predd_time)

	#choosing predictand observations that line up with predictor time
	hour = (predictor[0].metadata['FcstTime_hour']/3600) + lead_time
	days = len(predd_gmt)/24
	predd_hours = [0]*days
        k=0
        for i in range(len(predd_gmt)):
                if i%24 == hour:
			predd_hours[k]=predd_gmt[i]
			k+=1
	
	#catches when GFS data doesn't cover the last day of the month
	if len(predr_gmt) < len(predd_hours):
		predd_hours = predd_hours[:-1]	
	
	#find missing stations
	miss_stations = miss_station(predr_stations,predd_stations)
	stations = predd_stations
	
	#station and time array
	info = [['',''] for k in range(len(predr_gmt)*len(stations))]
	for i in range(len(predr_gmt)):
		for j in range(len(stations)):
			k = i*len(stations)+j
			info[k][0]=predr_gmt[i]
			info[k][1]=stations[j]

	#create column names
	names = ['']*(len(predictor)+len(predictand)+2)
	names[0]='Time'
	names[1]='Station'

	#creating array
	arr = np.zeros((len(stations)*len(predr_gmt),len(predictor)+len(predictand)))
	
	#adding predictor data
	for i in range(len(predictor)):
		#remove lead time and forecast reference time from variable name
		#and add variable name to column list of final dataframe
		if lead_time == 12:
			names[i+2]='GFS_'+predictor[i].get_variable_name()[:-11]
		else:
			 names[i+2]='GFS_'+predictor[i].get_variable_name()[:-10]

		#create pandas dataframe of data and sort alphabetically by station name
		predictor[i].data = np.squeeze(predictor[i].data,axis=2)
		predictor[i].data = pd.DataFrame(predictor[i].data,columns=predr_stations,index=predr_gmt)
		predictor[i].data = predictor[i].data.reindex(sorted(predictor[i].data.columns),axis=1)
		
		#remove stations with no predictand data
		k=0
		a=miss_stations[:]
		for j in predictor[i].data.columns:
			if not a:
				break
			if j==a[k]:
				predictor[i].data=predictor[i].data.drop(j,axis=1)
				del a[k]
		
		#add data to final dataframe
		for b in range(len(predr_gmt)):
			for c in range(len(stations)):
				k = b*len(stations)+c
				arr[k][i] = predictor[i].data.iloc[b][c]

	#add predictand data
	for i in range(len(predictand)):
		#removing extra underscore, adding variable name to column names
		names[len(predictor)+2+i]='METAR_'+predictand[i].get_variable_name()[:-1]
	
		#resize array and create pandas dataframe
		predictand[i].data = np.squeeze(predictand[i].data,axis=2)
		predictand[i].data = pd.DataFrame(predictand[i].data,columns=predd_stations,index=predd_hours)
		predictand[i].data = predictand[i].data.reindex(sorted(predictand[i].data.columns),axis=1)
		
		#remove extra days of predictand data
		predictand[i].data = predictand[i].data.iloc[0:len(predr_time),:]
			
		#add predictand data to array
		for b in range(len(predr_gmt)):
			for c in range(len(stations)):
				k = b*len(stations)+c
				val = predictand[i].data.iloc[b][c]
				
				#catch metar fill data
				if val == 9999: 
					val = np.nan
				arr[k][len(predictor)+i]=val
	
	#add station and time data to array and save as csv
	data = np.concatenate([info,arr],axis = 1)
	to_save = pd.DataFrame(data,columns=names)
	to_save.to_csv(str(start)+'_'+str(end)+'_'+str(lead_time)+'hrs.csv')
