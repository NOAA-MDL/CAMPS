#!/usr/bin/env python
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
import multiprocessing
#import metar_to_nc.util as util
from metar_to_nc.util import *
import metar_to_nc.qc_main as qc
import registry.util as cfg
from data_mgmt.Wisps_data import Wisps_data
import data_mgmt.Time as Time
import data_mgmt.writer as writer
import pdb



def main(control_file=None):
    """
    1. Reads control file
    2. Reads METAR and packages data into a station data type
    3. Preprocesses the station data
    4. QCs the observation data
    5. Postprocesses the station data
    6. Constructs an output NetCDF file
    7. Fills NetCDF file with QC'd obersvation data
    """
    # Read control file and assign vales
    if control_file:
        control = cfg.read_yaml(control_file)
        print "Reading Control File", control_file
    else:
        control = cfg.read_metar_control()
        print "Reading Default Control File"
    data_dir = control['METAR_data_directory']
    year = control['year']
    month = control['month']
    debug_level = control['debug_level']
    log_file = control['log_file']
    err_file = control['err_file']
    output_dir = control['nc_output_directory']
    def_path = control['station_defs']
    val_path = control['valid_stations']
    pickle = control['pickle']
    num_procs = control['num_processors']
    os.environ['NUM_PROCS'] = str(num_procs)
    
    num_procs = check_num_procs(num_procs)

    if log_file:
        out_log = open(log_file, 'w+')

        sys.stdout = out_log
        sys.stderr = out_log

    print "Starting main"

    # This will read the CSV files and put them into stations
    reader = read_obs(data_dir, year, month, def_path, val_path)

    # Convert all arrays to numpy arrays
    print "Converting station arrays to numpy arrays"
    stations = reader.station_list
    stations = convert_to_numpy(stations)
    fix_rounding_errors(stations)

    # Optionally pickle and save
    if pickle:
        print "Pickling"
        save_object(stations, 'stations.pkl')

    # Quality control the list of stations
    stations = qc.qc(stations, err_file)

    # Take off the start and end times from the arrays
    remove_time_buffer(stations)

    # Sort stations by station name
    stations = OrderedDict(sorted(stations.items()))

    # Create Output filename
    filename = output_dir
    filename += gen_filename(year, month)

    dimensions = cfg.read_dimensions()
    n_chars = dimensions['chars']
    num_stations = dimensions['nstations']
    time_dim = dimensions['time']

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
        wisps_obj.add_source('METAR')
        wisps_obj.change_data_type()
        wisps_obj.time = add_time(start_time, end_time)
        wisps_data.append(wisps_obj)

    wisps_obj = pack_station_names(stations.keys())
    wisps_obj.add_source('METAR')
    wisps_data.append(wisps_obj)

    extra_globals = get_globals()
    writer.write(wisps_data, filename, extra_globals)
    print "writing complete. Closing nc file"
    if log_file:
        out_log.close()

def check_num_procs(num_procs):
    max_cpu_count = multiprocessing.cpu_count()
    if num_procs > max_cpu_count:
        print "More processors specified than available"
        print "defaulting to number of processors available:", max_cpu_count
        return max_cpu_count
    return num_procs

def get_globals():
    """Returns a dictionary of global attributes for metar QC"""
    return {"source" : "Data from METAR with MDL Quality Control"}

def add_time(start, end, stride=None):
    time = []
    if stride == None: 
        stride = Time.ONE_HOUR
    pt = Time.PhenomenonTime(start, end, stride)
    # Result time will be PhenomenonTime
    rt = Time.ResultTime(start, end, stride,timedelta(seconds=0) ) 
    # Valid Time will be forever
    vt = Time.ValidTime(start, end, stride) 
        
    time.append(pt)
    time.append(rt)
    time.append(vt)
    return time

def pack_station_names(names):
    w_obj = Wisps_data('station')
    max_chars = max([len(i) for i in names])
    names = [ name+('_'*(max_chars - len(name))) for name in names]
    station_name_arr = np.array([])
    for name in names:
        char_arr = np.array(list(name), 'c')
        if len(station_name_arr) == 0: #if it's the first station
            station_name_arr = char_arr
        else:
            station_name_arr = np.vstack((station_name_arr,char_arr))
    w_obj.set_dimensions(tuple(['number_of_stations','num_characters']))
    w_obj.add_data(station_name_arr)
    w_obj.add_metadata("fill_value", '_')
    return w_obj
   
print __name__
if __name__ == "__main__":
    main()
