import sys
import os
from netCDF4 import Dataset
from datetime import datetime
from datetime import timedelta
from collections import OrderedDict
import pickle
import time
import numpy as np
import logging
import copy
import pdb

from ....registry import util as cfg
from metarreader import metarreader

from ... import util
from ... import Time

met_to_nc = cfg.read_metar_nc_lookup()
mar_to_nc = cfg.read_marine_lookup()

def save_object(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


def remove_time_buffer(station_list):
    """
    """
    for s in station_list.values():
        s.hours = s.hours[25:-2]
        for k, v in s.observations.iteritems():
            s.observations[k] = v[25:-2]


def parse_year_month(year_month):
    """
    Returns a two element string tuple of a combined yearmonth datestring.
    """
    if len(year_month) == 6:
        return (year_month[:4], year_month[4:])
    # This should be caught in control file reader
    raise IOError("year month string is not 6 characters. e.g. YYYYMM")


def get_data_type(predictor, nc_struct, obs_type='METAR'):
    """
    This routine will get the data type for the given predictor.
    The predictor is expected to be a CAMPS standard name for the
    obervation. Additionally, a dictionary entry 'data_type' needs to
    be defined in the netcdf configuration for this variable. The
    value for data_type should be a standard numpy data type.
    e.g. uint16, int8, _int, float, etc.
    """
    if obs_type == 'METAR':
        predictor = met_to_nc[predictor]
    elif obs_type == 'MARINE':
        predictor = mar_to_nc[predictor]
    if predictor in nc_struct.variables:
        predictor_config = nc_struct.variables[predictor]
        if 'data_type' in predictor_config:
            return predictor_config['data_type']
        else:
            logger.error("data_type is not defined for " + predictor)
            raise KeyError("data_type is not defined for " + predictor)
    else:
        raise KeyError("Observation: " + predictor +
                       " is not defined in NetCDF config file")


def scale_observation(observation, observation_array):
    """
    takes a METAR observation string and an associated array. If the scale
    factor is in the 'scale' dictionary, this function will scale the values
    of the array by that key value. This will NOT change the type of array.
    """
    scale = {
        'LON': 100,
        'LAT': 100,
        'VIS': 100,
        'MSL': 10,
        'ALT': 100
    }
    scale_factor = scale.get(observation, 1)
    if (scale_factor == 1):
        return observation_array

    def scale(value): return int(float(value) * scale_factor)
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


def convert_to_numpy(station_list,obs_type='METAR'):
    """
    Takes a dictionary of stations, loops through each of their observation
    arrays and converts them to numpy
    """
    nc_definitions = cfg.read_nc_config()
    for counter, station in enumerate(station_list.values()):
        for predictor, predictor_array in station.observations.iteritems():
            data_type = get_data_type(predictor,nc_definitions,obs_type=obs_type)
            # predictor_array = scale_observation(predictor,predictor_array)
            try:
                station.observations[predictor] = \
                    np.array(predictor_array, dtype=data_type)
            except:
                logging.warning("NumPy can't convert the array: "+predictor)
    return station_list


def read_obs(input_data,dates,stn_tbl,stn_lst,qc_flag):
    """
    Reads the observations from input.
    """
    one_hour = timedelta(hours=1)
    reader = metarreader(stn_tbl,stn_lst,filename=input_data)
    start_time = Time.str_to_datetime(dates[0])
    end_time = Time.str_to_datetime(dates[-1])

    # Apply the appropriate date buffers in order to perform QC.  QC requires 25 hours
    # before the first date and 2 hours after the last date.
    if qc_flag:
        start_buffer = Time.datetime_to_str(Time.str_to_datetime(dates[0])+timedelta(hours=-25))
        start_buffer_range = util.generate_date_range(start_buffer+'-'+dates[0]+','+'1h')
        end_buffer = Time.datetime_to_str(Time.str_to_datetime(dates[-1])+timedelta(hours=2))
        end_buffer_range = util.generate_date_range(dates[-1]+'-'+end_buffer+','+'1h')
        dates = start_buffer_range[:-1]+dates+end_buffer_range[1:]
        number_of_timesteps = len(dates)

    # Iterate through the input file.  A check is performed to make we have enough
    # data on input.
    for date in dates:
        #reader.read(date)
        #if reader.read_count == 1:
        #    if reader.obs_time > dates[0]:
        #       msg = "First date read not equal to expected first date "+dates[0]
        #       logging.error(msg)
        #       raise ValueError
        if reader.obs_time < date:
            reader.read(date)
        elif reader.obs_time >= date:
            reader.read(date,advance=False)
        #if reader.obs_time == dates[-1]:
        #   break

    # Post-process obs
    reader.check_latlon()
    return reader


def write_call(stations, call_var):
    station_name_arr = []
    for station_name, station in stations.iteritems():
        char_arr = np.array(list(station_name), 'c')
        if len(station_name_arr) == 0:
            station_name_arr = char_arr
        else:
            station_name_arr = np.vstack((station_name_arr, char_arr))
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
    for attribute, value in structured_config.iteritems():
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
    logging.info("Writing variables...")
    var_dict = {}
    MISSING_VALUE = 9999
    for name, var_info in structured_nc_format.iteritems():
        # Must have a 'name', 'data_type', and 'dimensions' key
        var_dims = tuple(var_info['dimensions'])  # needs to be a tuple
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
        nc_var = nc.createVariable(name, data_type, dimensions,
                                   zlib=True, complevel=7, shuffle=True,
                                   fill_value=9999)  # May want to change
        if 'attribute' in var_info:
            for attribute, value in var_info['attribute'].iteritems():
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
            logging.info("Variable "+var+"not in nc_variable.yaml list. Program will continue.")

    nc = open_file(filename)
    write_dims(dimensions, nc)
    write_globals(global_attributes, nc)
    var_dict = write_variables(variables, nc)
    return (nc, var_dict)


def gen_filename(year, month):
    """Generates the netcdf filename for METAR observations"""
    month = str(month).zfill(2)
    year = str(year)
    return "hre" + year + month + ".nc"
