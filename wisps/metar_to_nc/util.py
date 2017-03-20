import sys, os
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)

from netCDF4 import Dataset
from metarreader import metarreader
from datetime import datetime 
from datetime import timedelta
from collections import OrderedDict
import pickle
import time
import numpy as np
import logging
import copy
import registry.util as cfg


def save_object(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


def remove_time_buffer(station_list):
    """
    """
    print 'removing start and end buffers'
    for s in station_list.values():
        s.hours = s.hours[25:-2]
        for k,v in s.observations.iteritems():
            s.observations[k] = v[25:-2]

def parse_year_month(year_month):
    """
    Returns a two element string tuple of a combined yearmonth datestring.
    """
    if len(year_month) == 6:
        return (year_month[:4],year_month[4:])
    # This should be caught in control file reader
    raise IOError("year month string is not 6 characters. e.g. YYYYMM")

def get_data_type(predictor, nc_struct):
    """
    This routine will get the data type for the given predictor.
    The predictor is expected to be a WISPS standard name for the 
    obervation. Additionally, a dictionary entry 'data_type' needs to 
    be defined in the netcdf configuration for this variable. The 
    value for data_type should be a standard numpy data type.
    e.g. uint16, int8, _int, float, etc. 
    """
    predictor = cfg.metar_to_nc[predictor]
    if predictor in nc_struct.variables:
        predictor_config = nc_struct.variables[predictor]
        if 'data_type' in predictor_config:
            return predictor_config['data_type']
        else:
            logger.error("data_type is not defined for " + predictor)
            raise KeyError("data_type is not defined for " + predictor)
    else:
        raise KeyError("Observation: " + predictor + \
                      " is not defined in NetCDF config file")

def scale_observation(observation, observation_array):
    """
    takes a METAR observation string and an associated array. If the scale
    factor is in the 'scale' dictionary, this function will scale the values
    of the array by that key value. This will NOT change the type of array.
    """
    scale = {
            'LON' : 100,
            'LAT' : 100,
            'VIS' : 100,
            'MSL' : 10,
            'ALT' : 100
            }
    scale_factor = scale.get(observation, 1)
    if (scale_factor == 1):
        return observation_array
    scale = lambda value: int(float(value) * scale_factor)
    scaled_array = map(scale, observation_array)
    return scaled_array

def fix_rounding_errors(station_list):
    """
    Takes a dictionary of stations and
    rounds the float arrays
    """
    for station in station_list.values():
        msl = station.get_obs('MSL')
        alt = station.get_obs('ALT')
        vis = station.get_obs('VIS')
        np.around(msl, decimals=2, out=msl)
        np.around(alt, decimals=2, out=alt)
        np.around(vis, decimals=2, out=vis)


def convert_to_numpy(station_list):
    """
    Takes a dictionary of stations, loops through each of their observation
    arrays and converts them to numpy
    """
    nc_definitions = cfg.read_nc_config()
    for counter, station in enumerate(station_list.values()):
        if counter % 500 == 0:
            print "."
        for predictor, predictor_array in station.observations.iteritems():
            data_type = get_data_type(predictor, nc_definitions)
            #predictor_array = scale_observation(predictor,predictor_array)
            try:
                station.observations[predictor] = \
                    np.array(predictor_array, dtype=data_type)
            except: 
                print "numpy can't convert the array: " + predictor
    return station_list
            
def read_obs(data_dir, year, month, def_path, val_path, day=None, stride=None):
    """
    Reads the observations from a given year and month (optionally day and stride)
    Uses a metarreader to get the data fromthe ASCII files
    """
    if not day:
        day = 1 # start of the month
    # Define the extra time needed to be added to the 
    # start and end of the time period, due to QC
    one_hour = timedelta(hours=1)
    one_day = timedelta(days=1)
    start_buffer = one_day + one_hour 
    end_buffer = one_hour
    print "Reading observations"
    reader = metarreader(def_path, val_path)
    #start of given month
    start_time = datetime(year, month, day, 0)
    start_time = start_time - start_buffer
    current_time = copy.copy(start_time)
    if stride:
        end_time = start_time + timedelta(hours=stride)
    else:
        if month == 12:
            year += 1
            month = 0
        end_time = datetime(year, month+1, 1, 0) #full month
    end_time = end_time + end_buffer
    print "Start Time:", start_time
    number_of_timesteps = 0 
    init_time = time.time()
    while current_time <= end_time:
        if number_of_timesteps % 24 == 0:
            diff_time = time.time() - init_time 
            init_time = time.time()
            print "elapsed time: ", diff_time
            logging.info("processing: " + str(current_time))
            print "processing: " + str(current_time)
        time_str = current_time.strftime("%Y%m%d%H")
        number_of_timesteps += 1 
        reader.filename = data_dir + time_str
        reader.read()
        current_time += one_hour
    # Post-process obs
    reader.check_latlon()
    print "Filling in any holes in the stations"
    stations = reader.station_list
    for station_name, station in stations.iteritems():
        if len(station.hours) < number_of_timesteps:
            station.fill_empty_records(start_time, end_time, one_hour)
        if len(station.hours) > number_of_timesteps:
            raise ValueError("Something is very wrong, more station hours" \
                    "than actual hours")
    return reader   

def write_call(stations, call_var):
    station_name_arr = []
    for station_name, station in stations.iteritems():
        char_arr = np.array(list(station_name), 'c')
        if len(station_name_arr) == 0:
            station_name_arr = char_arr
        else:
            station_name_arr = np.vstack((station_name_arr,char_arr))
    call_var[:] = station_name_arr

def write_type(stations, type_var):
    station_type_arr = []
    for station_name, station in stations.iteritems():
        station_type_arr.append(station.type)
    station_type_arr = np.array(station_type_arr, dtype='uint8')
    type_var[:] = station_type_arr

def write_time(stations, time_var):
    """ Write the variety of time variables with dimensions of time """

    temp_station = stations[list(stations)[0]]
    time_list = temp_station.get_epoch_time()
    time_list = np.array(time_list, dtype='int64')
    time_var[:] = time_list

def write_dims(dimensions_dict, nc):
    """
    Writes nc dimensions that are packed into a structured format.
    The format is an array of dictionary objects where each dictionary 
    has a 'name' and a 'size' key, and values that match the name of
    the dimension and the size of that dimension respectively
    """
    for dimension in dimensions_dict.values():
        dim_size = 0
        if dimension == 'num_characters':
                dim_size = 4
        nc.createDimension(dimension, dim_size)

def write_globals(structured_config, nc):
    """
    Writes nc globals that are packed into a structured format.
    """
    for attribute,value in structured_config.iteritems():
        setattr(nc, attribute, value)

def real_nc_data_type(data_type):
    """
    Returns True if data_type is allowable in numpy
    """
    return True

def write_variables(structured_nc_format, nc):
    """
    Writes metar variables to netcdf file handle
    """
    print 
    print "writing variables"
    print 
    var_dict = {}
    MISSING_VALUE = 9999
    for name, var_info in structured_nc_format.iteritems():
        # Must have a 'name', 'data_type', and 'dimensions' key
        var_dims = tuple(var_info['dimensions']) #needs to be a tuple
        var_dims = cfg.read_dimensions()
        num_stations = var_dims['n_stations_dimension']
        time_dim = var_dims['time_dimension']
        dimensions = (num_stations, time_dim)
        if name == 'observation_time':
            dimensions = (var_dims['time_dimension'])
        if name == 'station_name':
            n_chars = var_dims['number_of_chars_dimension']
            num_stations = var_dims['n_stations_dimension']
            dimensions = (num_stations, n_chars)

        data_type = var_info['data_type']
        if not real_nc_data_type(data_type):
            raise Exception('not a real netcdf data_type')
        #print "creating variable: " + name
        nc_var = nc.createVariable(name, data_type, dimensions, \
                                zlib=True, complevel=7, shuffle=True,\
                                fill_value=9999) # May want to change
        if 'attribute' in var_info:
            for attribute,value in var_info['attribute'].iteritems():
                setattr(nc_var, attribute, value)
        var_dict[name] = nc_var
    return var_dict

def open_file(filename):
    """Opens a netcdf file with a given filename"""
    return Dataset(filename, "w", format="NETCDF4")

def init_netcdf_output(filename):
    """ 
    Initializes the structure of the output netCDF file.
    """
    # Read YAML config for netcdf structure and properties
    nc = cfg.read_nc_config()
    dimensions = nc.dimensions
    global_attributes = nc.global_attributes

    # Filter out only METAR variables
    variables = {}
    all_variables = nc.variables
    metar_variables = cfg.read_metar_lookup()
    for var in metar_variables.keys():
        try:
            variables[var] = all_variables[var]
        except:
            print "variable,", var, "not in nc_variable.yml list"
            print "continuing"
        
    nc = open_file(filename) 
    write_dims(dimensions,nc)
    write_globals(global_attributes,nc)
    var_dict = write_variables(variables, nc)
    return (nc, var_dict)

def gen_filename(year, month):
    """Generates the netcdf filename for METAR observations"""
    month = str(month).zfill(2)
    year = str(year)
    return "hre"+year+month+".nc"

#main()








