
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
    data_dir = control["METAR_data_directory"]
    year = control["year"]
    month = control["month"]
    debug_level = control['debug_level']
    log_file = control['log_file']
    output_dir = control['nc_output_directory']

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
    nc,var_dict = init_netcdf_output(filename)

    # Handle special case variables.
    # 'CALL' has char dimension, 'TYPE' and 'Time' have 1 dimension.
    # Write these variables to the NetCDF file.
    call_var = var_dict.pop('station', 0)
    time_var = var_dict.pop('observation_time', 0)
    write_call(stations,call_var)
    write_time(stations,time_var)

    # formats each observation into a 2D array with
    # dimensions of # of stations and time
    print "Construct 2D arrays"
    for observation_name, nc_var in var_dict.iteritems():
        # Set the observation name to the standard WISPS name
        try :
            observation_name = cfg.nc_to_metar[observation_name]
        except :
            print "ERROR: cannot find the netcdf equivalent of " +observation_name +\
                    "in METAR lookup table. Skipping."

        temp_obs = []
        for station_name, cur_station in stations.iteritems():
            station_data = cur_station.observations[observation_name] 
            if len(temp_obs) == 0:
                temp_obs = station_data
            else:
                temp_obs = np.vstack((temp_obs, station_data)) # takes tuple arg
        try:
            nc_var[:] = temp_obs
        except TypeError as e:
            print "observation contains a decimal when integer type. skipping"
            print e
        except ValueError as e:
            print "observation likely includes a string. skipping"
            print e
    print "writing complete. Closing nc file"
    nc.close()


