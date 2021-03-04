#!/usr/bin/env python
import sys
import os
import time
import numpy as np
import logging
from collections import OrderedDict
import pdb
from netCDF4 import Dataset
from datetime import datetime, timedelta

from ..core import Camps_data
from ..core import Time as Time
from ..core import writer as writer
from ..core import util
from ..core.data_conversion.marine_to_nc.marinereader import marinereader
from ..core.data_conversion.metar_to_nc.util import convert_to_numpy
from ..registry import util as cfg


def main():
    """Main function for converting marine CSV file to CAMPS netCED file."""

    import sys
    control_file = None if len(sys.argv) != 2 else sys.argv[1]

    # Read control file and assign vales
    if control_file:
        control = cfg.read_yaml(control_file)
        print(("Reading Control File: "+control_file))

    date_range = control['date_range']
    input_data = control['input_data']
    output = control['output']
    debug_level = control['debug_level']
    log_file = control['log_file']
    station_list = control['station_list']
    station_table = control['station_table']

    # Threading not necessary in marine_to_nc
    #num_procs = control['num_processors']
    #os.environ['NUM_PROCS'] = str(num_procs)
    #num_procs = check_num_procs(num_procs)

    if log_file:
        out_log = open(log_file, 'w+')
        sys.stdout = out_log
        sys.stderr = out_log

    try:
        logging.getLogger('').handlers = []
        level = logging.getLevelName(debug_level)
        logging.basicConfig(level=level)
    except:
        print("Logging setup failed")
        raise

    logging.info("Starting main")

    # Create date list and read station list and table
    dates = util.generate_date_range(date_range)
    stn_lst = util.read_station_list(station_list)
    stn_lst,stn_tbl = util.read_station_table(station_table,stn_lst)

    # Create lat and lon arrays from station information
    lats, lons = map(list,zip(*[(lst['lat'],lst['lon']) for i,lst in enumerate(list(stn_tbl.values())) if list(stn_tbl.keys())[i] in stn_lst]))
 

    # Read all marine observations
    reader = marinereader(stn_tbl,stn_lst,filename=input_data)
    start_date = dates[0]
    end_date = dates[-1]
    reader.read(end_date=end_date)

    # Convert all arrays to numpy arrays
    logging.info("Converting station arrays to numpy arrays")
    stations = reader.station_list
    stations = convert_to_numpy(stations,obs_type='MARINE')

    # Sort stations by station name
    stations = OrderedDict(sorted(stations.items()))

    # Create Output filename
    filename = output

    dimensions = cfg.read_dimensions()
    num_stations = dimensions['nstations']
    time_dim = dimensions['time']
    # Create a list of Camps data objects, one object for each
    # observed parameter
    camps_data = []

    lat_obj = Camps_data('latitude')
    lat_obj.set_dimensions((num_stations,))
    lat_obj.data = np.array(lats)
    lon_obj = Camps_data('longitude')
    lon_obj.set_dimensions((num_stations,))
    lon_obj.data = np.array(lons)

    camps_data.append(lat_obj)
    camps_data.append(lon_obj)

    obs = reader.observations
    obs.remove('TIME')
    start_time = start_date
    end_time = end_date
    mar_to_nc = cfg.read_marine_lookup()
    for obs_name in obs:
        # Set the observation name to the standard CAMPS name
        try:
            observation_name = mar_to_nc[obs_name]
        except:
            logging.error("Cannot find the CAMPS-NetCDF standard name equivalent of " +
                          obs_name +
                          "in marine_to_nc lookup table. Skipping.")
            continue

        # Loop through the stations and stitch together the current observation
        temp_obs = []
        for station_name, cur_station in stations.items():
            temp_obs.append(cur_station.get_obs(obs_name))
        obs_data = np.array(temp_obs)

        logging.info(observation_name)

        # Construct Camps data object for particular observed variable
        camps_obj = Camps_data(observation_name)
        if camps_obj.is_feature_of_interest() and len(obs_data.shape)>1:
            obs_data = obs_data[:,0]
            camps_obj.set_dimensions((num_stations,))
        else:
            camps_obj.set_dimensions((time_dim,num_stations))
        camps_obj.add_data(obs_data)
        camps_obj.add_source('NDBC')
        camps_obj.add_process('ProcMarine')
        camps_obj.add_process('MarineQC')
        camps_obj.change_data_type()

        try:
            camps_obj.metadata['vertical_coord'] = camps_obj.metadata.pop('coordinates')
        except:
            pass
        # Again check for time bounds, pass extra info to add_time if
        # there are time bounds
        if not camps_obj.is_feature_of_interest():
            if camps_obj.has_time_bounds():
                hours = camps_obj.properties['hours']
                camps_obj.metadata['hours'] = hours
                camps_obj.time = add_time(start_time, end_time, time_bounds=hours)
            else:
                camps_obj.time = add_time(start_time, end_time)

        # Transpose the array and swap dimension names. Note that this may be a
        # temporary solution.
        if len(camps_obj.data.shape)>1:
            camps_obj.data = np.transpose(camps_obj.data)
        camps_data.append(camps_obj)

    # Fill in object with common metadata and append to list
    camps_obj = pack_station_names(list(stations.keys()))
    camps_obj.add_source('NDBC')
    camps_data.append(camps_obj)

    # Write list of Camps data objects to netCDF4 file
    extra_globals = get_globals()
    writer.write(camps_data, filename, extra_globals)

    if log_file:
        out_log.close()


def add_time(start, end, stride=None, time_bounds=None):
    """Create and return PhenomenonTime objects, if the observation is instantaneous,
    or PhenomenonTimePeriod objects, if the observation spans a time period."""

    time = []
    if stride is None:
        stride = Time.ONE_HOUR

    if time_bounds:
        pt = Time.PhenomenonTimePeriod(start_time=start, end_time=end, stride=stride, period=time_bounds)
    else:
        pt = Time.PhenomenonTime(start_time=start, end_time=end, stride=stride)
    time.append(pt)

    return time


def get_globals():
    """Returns a dictionary of global attributes for marine QC"""

    return {"source": "Data from NDBC with their quality control procedures."}


def pack_station_names(names):
    """Constructs and returns a Camps data object for station data. """

    # Instantiate the object
    w_obj = Camps_data('stations')

    # Construct station data array
    max_chars = max([len(i) for i in names])
    names = [name + ('_' * (max_chars - len(name))) for name in names]
    station_name_arr = np.array([])
    if len(names) == 1:
        char_arr = np.array(list(names[0]))
        station_name_arr = np.reshape(char_arr,(len(char_arr.shape),char_arr.shape[0]))
    elif len(names) > 1:
        station_name_arr = np.array(names)

    # Fill in the object with appropriate data.
    w_obj.set_dimensions(tuple(['stations']))
    w_obj.add_data(station_name_arr)
    w_obj.add_metadata("fill_value", '_')
    w_obj.add_metadata("comment","NDBC stations consist of buoy, C-MAN, and platform drilling sites")
    w_obj.add_metadata("long_name","NDBC station identifiers")

    return w_obj


if __name__ == "__main__":
    main()
