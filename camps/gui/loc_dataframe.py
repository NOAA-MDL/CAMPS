#!/usr/bin/env python
import os
import sys
from netCDF4 import Dataset
import numpy as np
import numpy.ma as ma
import pandas as pd
from datetime import datetime
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

def loc_stations(station_let,lat,lon):
        """
	merges station letters into single list of station names
	"""
       
	stat = [['',0,0] for k in range(np.size(station_let,0))]
        print len(stat)
        for i in range(len(stat)):
                for j in range(4):
                        if station_let[i][j] is not np.ma.masked:
                                stat[i][0]+=station_let[i][j]
                try:
                        stat[i][1]=lat[i][0]
                        stat[i][2]=lon[i][0]
                except:
                        stat[i][1]=lat[i]
                        stat[i][2]=lon[i]
        return stat

def gmt(time):
	"""
	converts time to gmt, appends to list
	"""
        gmt = [0]*time.size
        for i in range(time.size):
                gmt[i]=datetime.utcfromtimestamp(time[i]).strftime('%Y-%m-%d %H:%M:%S')
        return gmt

def loc_dataframe(LCOlat,UCOlat,LCOlon,UCOlon):
        """
	builds and saves dataframe to be used for graphs
	inputs are lats and lons for region
        """
	global loc_stations
        global gmt
        global miss_station

	#read control files
	control = cfg.read_yaml('../registry/graphs_test.yaml')
	pred_ctrl = cfg.read_yaml(cfg.get_config_path(control.pred_file))
	predd_ctrl = cfg.read_yaml(cfg.get_config_path(control.predd_file))

	#get paths to data and update database
	predictor_file_path = control.predictor_file_path
	predictand_file_path = control.predictand_file_path
	pred_file_id = update(predictor_file_path[0])
	predd_file_id = update(predictand_file_path[0])
	
	#stores lead time and date range
	lead_time = control.lead_time
	date_range = control.date_range

	#store info for fetch many dates
	start,end,stride = read_pred.parse_range(date_range[0])
	stride = timedelta(seconds=int(stride))
        start = Time.str_to_datetime(start)
        end = Time.str_to_datetime(end)
	fcst_ref_time = control.date_range[0].split('-')[0][-2:]
	
	#intializes list of predictors
	pred_list = pred_ctrl.predictors
	predictor = []
	
	#loops though predictors and creates camps data objects
	for entry_dict in pred_list:
		#formats metadata
		pred = create.preprocess_entries(entry_dict, fcst_ref_time)
		
		#adds info to metadata that's not currently stored
		pred.search_metadata['reserved2'] = lead_time
                pred.search_metadata['file_id'] = pred_file_id
		pred.search_metadata['reserved1'] = 'vector'

		#builds camps data objects for each day
		variable = fetch_many_dates(predictor_file_path,start,end,stride,pred.search_metadata)
		
		#appends data to single camps data object
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

	#loops through predictands and builds camps data objects
        for entry_dict in predd_list:
		#formats metadata
        	vertical_coordinate = entry_dict.pop('Vertical_Coordinate')
		entry_dict['file_id'] = predd_file_id
                
		#builds camps data object for each day
		variable = fetch_many_dates(predictand_file_path,start, end, stride, entry_dict)
                
		#appends data to single camps data object
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
	predr_lat = predr.variables['latitude'][:]
        predr_lon = predr.variables['longitude'][:]
        predr_time_name = predictor[0].ancillary_variables.split(' ')[0]
        predr_time = predr.variables[predr_time_name][:]
        predr.close()

        #reformatting predictor station,location, and time data
        predr_stat_loc = loc_stations(predr_stat,predr_lat,predr_lon)
        predr_stations = [i[0] for i in predr_stat_loc]
        predr_gmt = gmt(predr_time)

        #getting predictand station and time data
        predd = Dataset(predictand_file_path[0])
        predd_stat = predd.variables['station'][:]
	predd_lat = predd.variables['latitude'][:]
        predd_lon = predd.variables['longitude'][:]
        predd_time_name = predictand[0].ancillary_variables.split(' ')[0]
        predd_time = predd.variables[predd_time_name][:]
        predd.close()

        #unmask and set up lat/lon arrays
        predd_lat = predd_lat[0,:]
        predd_lon = predd_lon[0,:]
        predd_lat.mask = ma.nomask
        predd_lon.mask = ma.nomask 
        
        #reformatting predictand station, location, and time data
        predd_stat_loc = loc_stations(predd_stat,predd_lat,predd_lon)
        predd_stations = [i[0] for i in predd_stat_loc]
        predd_gmt = gmt(predd_time)

        new_predd_time = [int((datetime.strptime(predd_gmt[i], '%Y-%m-%d %H:%M:%S')-datetime(1970,1,1)).total_seconds()) for i in range(len(predd_gmt))]
        predd_loc = [np.where(n == np.array(new_predd_time))[0][0] for n in predr_time]
        predd_hours = [np.array(predd_gmt)[predd_loc]]    

        #find missing stations
        stations = np.intersect1d(predr_stations, predd_stations)
        predd_order = [np.where(i == np.array(predd_stations))[0][0] for i in stations]
        predr_order = [np.where(i == np.array(predr_stations))[0][0] for i in stations]

        #reorder lat/lon arrays
        predd_lat = predd_lat[predd_order]
        predd_lon = predd_lon[predd_order]
        
        #find stations in location bounds
        loc_stations = ['']*len(stations)
        index = []
        k = 0
        for i in range(len(stations)):
                if predd_lat[i] > LCOlat and predd_lat[i] < UCOlat and predd_lon[i] > LCOlon and predd_lon[i] < UCOlon:  
                    loc_stations[k] = stations[i]
                    index.append(i)
                    k += 1
        loc_stations = loc_stations[:k]

        #station and time array
        info = [['',''] for k in range(len(predr_gmt)*len(loc_stations))]
        for i in range(len(predr_gmt)):
                for j in range(len(loc_stations)):
                        k = i*len(loc_stations)+j
                        info[k][0]=predr_gmt[i]
                        info[k][1]=loc_stations[j]

        #create column names
        names = ['']*(len(predictor)+len(predictand)+2)
        names[0]='Time'
        names[1]='Station'

        #creating array
        arr = np.zeros((len(loc_stations)*len(predr_gmt),len(predictor)+len(predictand)))
	
        #adding predictor data
        for i in range(len(predictor)):
		#add variable name to column list of final dataframe
                names[i+2]='GFS_'+predictor[i].get_variable_name()
			
		#create pandas dataframe of data and sort alphabetically by station name
                predictor[i].data = predictor[i].data[:,np.array(predr_order)[index]]
		predictor[i].data = np.squeeze(predictor[i].data,axis=2)
                predictor[i].data = pd.DataFrame(predictor[i].data,columns=loc_stations,index=predr_gmt)
                predictor[i].data = predictor[i].data.reindex(sorted(predictor[i].data.columns),axis=1)

                #add data to final dataframe
		for b in range(len(predr_gmt)):
			#n=0
                        for c in range(len(loc_stations)):
                                k = b*len(loc_stations)+c
                                arr[k][i] = predictor[i].data.iloc[b][c]
        #add predictand data
        for i in range(len(predictand)):
        	#removing extra underscore, adding variable name to column names
                names[len(predictor)+2+i]='METAR_'+predictand[i].get_variable_name()[:-1]
               	
		#resize array, create pandas dataframe
                #orientation as predictor data, and sort by station
                predictand[i].data = predictand[i].data[:,np.array(predd_order)[index]]
                predictand[i].data = np.squeeze(predictand[i].data,axis=2)
                predictand[i].data = pd.DataFrame(predictand[i].data,columns=loc_stations,index=predd_hours)
                predictand[i].data = predictand[i].data.reindex(sorted(predictand[i].data.columns),axis=1)

                #add predictand data to array
                for b in range(len(predr_gmt)):
			#n=0
                        for c in range(len(loc_stations)):
                                k = b*len(loc_stations)+c
                                val = predictand[i].data.iloc[b][c]
                                #catch metar fill data
                                if val == 9999:
                                    val = np.nan
                                arr[k][len(predictor)+i]=val

        #add station and time data to array and save as csv
        data = np.concatenate([info,arr],axis = 1)
        to_save = pd.DataFrame(data,columns=names)
        to_save.to_csv(control.output_file_path+'loc_'+start.strftime("%Y%m%d%H")+'_'+end.strftime("%Y%m%d%H")+'_'+str(lead_time)+'hrs_'+str(LCOlat)+'_'+str(UCOlat)+'_'+str(LCOlon)+'_'+str(UCOlon)+'.csv')
