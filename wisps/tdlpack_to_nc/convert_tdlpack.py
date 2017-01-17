#!/usr/bin/env python
import sys, os
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)

import pytdlpack as ptdl
import yaml
import time
import numpy as np
import argparse
from netCDF4 import Dataset
import pdb
from datetime import datetime
import registry.util as cfg
import metar_to_nc.util as util
from collections import OrderedDict

MISSING_VALUE = 9999

class point:
    def __init__(self,name,obs_types,num_timesteps):
        self.name = name
        self.dates = np.zeros(num_timesteps)
        self.predictors = {}
        for o in obs_types:
            self.predictors[o] = np.full((num_timesteps),MISSING_VALUE)
    
    def add_predictor(self, predictor_id):
        self.predictors[predictor_id] = np.full((len(self.dates)),MISSING_VALUE)


def get_point_list(points):
    """ Returns a 4 by n charactar array representing the name of the point """
    for p in points:
        np.array

def parse_grid_definition(grid_def):
    """ 
    Parses a grid definition section array that is in 
    a ptdl record. Returns dictionary. 
    """
    grid_definition = {}
    grid_definition['section_length'] = grid_def[0]
    grid_definition['map_projection'] = grid_def[1]
    grid_definition['NX'] = grid_def[2]
    grid_definition['NY'] = grid_def[3]
    grid_definition['lower_left_lat'] = grid_def[4] # degrees * 10000
    grid_definition['lower_left_lon'] = grid_def[5] # degrees * 10000
    grid_definition['grid_orientation'] = grid_def[6] # degrees * 10000
    grid_definition['grid_length'] = grid_def[7]  # in mm
    grid_definition['lat_at_grid_length'] = grid_def[8] # 
    return grid_definition

def parse_product_definition(prod_def):
    product_definition = {}
    product_definition['section_length'] = prod_def[0]
    product_definition['grid_defined'] = prod_def[1]
    product_definition['year'] = prod_def[2]
    product_definition['month'] = prod_def[3]
    product_definition['day'] = prod_def[4]
    product_definition['hour'] = prod_def[5]
    product_definition['minutes'] = prod_def[6]
    product_definition['formatted_date'] = prod_def[7]
    product_definition['id_1'] = prod_def[8]
    product_definition['id_2'] = prod_def[9]
    product_definition['id_3'] = prod_def[10]
    product_definition['id_4'] = prod_def[11]
    product_definition['projection_hours'] = prod_def[12] #hours
    product_definition['projection_minutes'] = prod_def[13]
    product_definition['model'] = prod_def[14]
    product_definition['sequence_number'] = prod_def[15]
    product_definition['decimal_scale_factor'] = prod_def[16]
    product_definition['binary_scale_factor'] = prod_def[17]
    return product_definition

def write_model_to_netcdf(filepath, var_dict):
    nc = Dataset(filename, mode='w', format="NETCDF4")
    for i in var:
        pdb.set_trace()



def write_obs_to_netcdf(filepath, point_dict):
    """
    Writes a Point dictionary of objects to a netcdf file.
    Expects point_dict to have the same shape and number of 
    predictors.
    """
    cfg.read_nc_config()
    mosID_lookup = cfg.read_mosID_lookup()
    temp_obs = []
    nc,var_dict = util.init_netcdf_output(filepath)
    all_predictors = point_dict.values()[0].predictors.keys() #mosIDs
    sorted_point_dict = OrderedDict(sorted(point_dict.items()))
    all_points = sorted_point_dict.values()
    all_names = sorted_point_dict.keys()
    for p in all_predictors:
        try:
            nc_var_name = mosID_lookup[p]
        except KeyError: 
            print p.name + " is not in mosID->netcdf lookup table. Skipping."
        temp_obs = []
        for v in all_points:
            cur_data = v.predictors[p]
            if len(temp_obs) == 0:
                temp_obs = cur_data
            else:
                temp_obs = np.vstack((temp_obs,cur_data))
        try:
            var_dict[nc_var_name][:] = temp_obs
        except TypeError as e:
            print "Observation, "+nc_var_name+", is a different type from what is defined in config."
            print e
        except ValueError as e: 
            print "Observation, "+nc_var_name+", contains a string. Skipping."
            print e
        except KeyError as e:
            print "MOS ID does not equal valid WISPS variable name"
    write_station_names(var_dict, all_names)
    print "Finished writing NetCDF file"
    nc.close()

def write_station_names(var_dict, names):
    """
    Write station names.
    """
    station_name_arr = []
    for name in names:
        char_arr = np.array(list(name), 'c')
        if len(station_name_arr) == 0:
            station_name_arr = char_arr
        else:
            station_name_arr = np.vstack((station_name_arr,char_arr))
    var_dict['station'][:] = station_name_arr

def is_obs_tdl_file(tdl_filepath):
    """ 
    Returns True if is detects that the file is an obs file
    """
    return 'gfs' not in tdl_filepath

def convert_model(filepath, out_dir="./"):
    """
    Converts TDL pack at location filepath to netcdf.
    """
    records = ptdl.TdlpackDecode(filepath)
    var_dict = {} # forecast time <= 192
    alt_var_dict = {} # forecast time > 192
    pdb.set_trace()
    for i,r in enumerate(records):
        name = r.plain_language.strip()
        data = r.unpackData()
        if r.product_definition_section[10] <= 192:
            cur_dict = var_dict
        else:
            cur_dict = alt_var_dict

        if name not in cur_dict:
            cur_dict[name] = data
        else:
            try:
                cur_dict[name] = np.dstack((cur_dict[name],data))
            except Exception as e:
                pdb.set_trace()
        if i % 50 == 0:
            print i, len(data)
    pdb.set_trace()
    return var_dict


def convert_obs(filepath, out_dir="./"):
    if not os.path.isfile(filepath):
        print "file: " +filepath+ " Not found"
        return
    point_dict = {}
    records = ptdl.TdlpackDecode(filepath)
    obs_types = find_all_obs_types(records)
    num_timesteps = find_number_of_timesteps(records)
    print "number of timesteps ", num_timesteps
    time_index = 0
    cur_date = records[0].date
    init_time = time.time()
    for rnum,r in enumerate(records):
        if r.date != cur_date:
            #if int(r.date) % 10 == 0:
            #    ## Time test ##
            #    diff_time = time.time() - init_time
            #    init_time = time.time()
            #    print 'elapsed time:',diff_time
            #    ## ## ## ## ## ##
            print cur_date
            print time_index
            time_index += 1
            cur_date = r.date
        record = r.values
        for i,call in enumerate(r.ccall):
            if call not in point_dict:
                new_point = point(call,obs_types,num_timesteps)
                new_point.dates[time_index] = r.date
                point_dict[call] = new_point

            cur_point = point_dict[call]
            str_id = str(r.id[0])
            cur_point.predictors[str_id][time_index] = record[i]

    write_obs_to_netcdf(out_dir + os.path.basename(filepath)+".nc", point_dict)

def find_number_of_records_in_one_timestep(records):
    start_date = records[0].date
    for i,r in enumerate(records):
        if r.date != start_date:
            return i

def find_all_obs_types(records):
    obs_types = set()
    for r in records:
        obs_types.add(str(r.id[0]))
    return obs_types

def find_number_of_timesteps(records):
    first_record = records[0]
    last_record = records[-1]
    first_record_date = parse_hour_to_datetime(first_record.date)
    last_record_date = parse_hour_to_datetime(last_record.date)
    delta_time = last_record_date - first_record_date
    steps = delta_time.days * 24
    print "steps: ",  steps
    print "delta_time: ",delta_time.days 
    steps += delta_time.seconds/60/60
    print "steps: ",steps
    return steps+1
    
def parse_hour_to_datetime(str_date):
    """
    Assumed that time is in form YYYYMMDDHH, which is the format of the
    hours array.
    """
    str_date = str(str_date)
    year = int(str_date[:4])
    month = int(str_date[4:6])
    day = int(str_date[6:8])
    hour =  int(str_date[8:10])
    return datetime(year,month,day,hour)

### MAIN ###
