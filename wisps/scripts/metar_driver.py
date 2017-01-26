
# Add a relative path
import sys, os
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)

import numpy as np
import logging
from netCDF4 import Dataset
from datetime import datetime 
from datetime import timedelta
from collections import OrderedDict
#import metar_to_nc.util as util
from metar_to_nc.util import *
import metar_to_nc.qc_main as qc
import registry.util as cfg
from data_mgmt.Wisps_data import Wisps_data
import data_mgmt.Time as Time
import data_mgmt.writer as writer

def main():
    """
    1. Reads control file
    2. Reads METAR and packages data into a station data type
    3. Preprocesses the station data
    4. QCs the observation data
    5. Postprocesses the station data
    6. Constructs an output NetCDF file
    7. Fills NetCDF file with QC'd obersvation data
    """
    print "Starting main"
    #cfg.read_nc_config()
    # Read control file and assign vales
    control = cfg.read_metar_control()
    data_dir = control['METAR_data_directory']
    year = control['year']
    month = control['month']
    debug_level = control['debug_level']
    log_file = control['log_file']
    output_dir = control['nc_output_directory']
    pickle = control['pickle']

    # This will read the ASCII files and put them into stations
    reader = read_obs(data_dir, year, month)

    # Convert all arrays to numpy arrays
    # Note: The reason I'm not initializing these as numpy arrays
    #       is because I would need to know its size in advance.
    print "Converting station arrays to numpy arrays"
    stations = reader.station_list
    stations = convert_to_numpy(stations)
    fix_rounding_errors(stations)

    # Optionally pickle and save
    if pickle:
        print "Pickling"
        save_object(stations, 'stations.pkl')

    # Quality control the list of stations
    stations = qc.qc(stations)

    # Take off the start and end times from the arrays
    remove_time_buffer(stations)

    # Sort stations by station name
    stations = OrderedDict(sorted(stations.items()))

    # Initialize the NetCDF file. 
    # 'nc' is the filehandle.
    # 'var_dict' is the netcdf variable objects
    filename = output_dir
    filename += gen_filename(year, month)

    dimensions = cfg.read_dimensions()
    n_chars = dimensions['chars']
    num_stations = dimensions['nstations']
    time_dim = dimensions['time']
    #nc,var_dict = init_netcdf_output(filename)

    # Handle special case variables.
    write_call(stations,call_var)

    # formats each observation into a 2D array with
    # dimensions of # of stations and time
    if pickle:
        print "Pickling"
        save_object(stations, 'postqc.pkl')
    print "Construct 2D arrays"
    wisps_data = []
    example_station = stations.values()[0]
    obs = example_station.observations.keys()
    obs.remove('TIME')
    start_time = example_station.hours[0]
    end_time = example_station.hours[-1]
    print "start time", start_time
    print "end time", end_time
    #for metar_name, nc_var in var_dict.iteritems():
    for metar_name in obs:
        # Set the observation name to the standard WISPS name
        try :
            observation_name = cfg.metar_to_nc[metar_name]
        except :
            print "ERROR: cannot find the netcdf equivalent of " +metar_name +\
                    "in METAR lookup table. Skipping."
            continue
        # Loop through the stations and stitch together the current observation
        temp_obs = []
        for station_name, cur_station in stations.iteritems():
            station_data = cur_station.get_obs(metar_name)
            if len(temp_obs) == 0: #If the first station
                temp_obs = station_data
            else:
                temp_obs = np.vstack((temp_obs, station_data)) # takes tuple arg
        print observation_name
        wisps_obj = Wisps_data(observation_name)
        wisps_obj.set_dimensions()
        wisps_obj.add_data(temp_obs)
        wisps_obj.change_data_type()
        wisps_obj.time = add_time(start_time, end_time)
        wisps_data.append(wisps_obj)
 

    writer.write(wisps_data, filename)
    print "writing complete. Closing nc file"

def add_time(start, end, stride=None):
    time = []
    if stride == None: 
        stride = Time.ONE_HOUR
    pt = Time.PhenomenonTime(start, end, stride)
    rt = Time.ResultTime(start, end, stride) # Result time will be now
    vt = Time.ValidTime(start, end, stride)
        
    time.append(pt)
    time.append(rt)
    time.append(vt)
    return time

def alt_func(stations):

    print "Construct 2D arrays"
    wisps_data = []
    example_station = stations.values()[0]
    obs = example_station.observations.keys()
    obs.remove('TIME')
    start_time = example_station.hours[0]
    end_time = example_station.hours[-1]
    #for metar_name, nc_var in var_dict.iteritems():
    for metar_name in obs:
        # Set the observation name to the standard WISPS name
        try :
            observation_name = cfg.metar_to_nc[metar_name]
        except :
            print "ERROR: cannot find the netcdf equivalent of " +metar_name +\
                    "in METAR lookup table. Skipping."
            continue
        # Loop through the stations and stitch together the current observation
        temp_obs = []
        for station_name, cur_station in stations.iteritems():
            station_data = cur_station.get_obs(metar_name)
            if len(temp_obs) == 0: #If the first station
                temp_obs = station_data
            else:
                temp_obs = np.vstack((temp_obs, station_data)) # takes tuple arg
        print observation_name
        wisps_obj = Wisps_data(observation_name)
        wisps_obj.set_dimensions()
        wisps_obj.add_data(temp_obs)
        wisps_obj.change_data_type()
        wisps_obj.time = add_time(start_time, end_time)
        wisps_data.append(wisps_obj)
 

    writer.write(wisps_data, 'test.nc')
    print "writing complete. Closing nc file"
