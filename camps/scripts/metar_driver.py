#!/usr/bin/env python
import sys
import os
import numpy as np
import logging
from collections import OrderedDict
import multiprocessing
import pdb
from netCDF4 import Dataset
from datetime import datetime, timedelta

from ..core.data_conversion.metar_to_nc.util import *
from ..core.data_conversion.metar_to_nc import qc_main
from ..registry import util as cfg
from ..core.Camps_data import Camps_data
from ..core import Time as Time
from ..core import writer as writer
from ..core import util

def main():
    """
    1. Reads control file
    2. Reads METAR and packages data into a station data type
    3. Preprocesses the station data
    4. QCs the observation data
    5. Postprocesses the station data
    6. Constructs an output NetCDF file
    7. Fills NetCDF file with QC'd observation data
    """

    # Read control file and assign values
    import sys
    control_file = None if len(sys.argv) != 2 else sys.argv[1]
    if control_file is not None:
        control = cfg.read_yaml(control_file)
        logging.info("Control File: " + str(control_file) + " successfully read")
    else:
        raise RuntimeError("A control file must be provided for camps_metar_to_nc.  Exiting program.")

    # Read contents of control file
    date_range = control['date_range']
    input_data = control['input_data']
    output = control['output']
    debug_level = control['debug_level']
    log_file = control['log_file']
    err_file = control['err_file']
    station_list = control['station_list']
    station_table = control['station_table']
    qc_flag = control['qc_flag']
    pickle = control['pickle']

    num_procs = control['num_processors']
    os.environ['NUM_PROCS'] = str(num_procs)
    num_procs = check_num_procs(num_procs)

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

    dates = util.generate_date_range(date_range)
    stn_lst = util.read_station_list(station_list)
    stn_lst,stn_tbl = util.read_station_table(station_table,stn_lst)

    # This will read the CSV files and put them into stations
    reader = read_obs(input_data,dates,stn_tbl,stn_lst,qc_flag)

    # Convert all arrays to numpy arrays
    logging.info("Converting station arrays to numpy arrays")
    stations = reader.station_list
    stations = convert_to_numpy(stations)
    fix_rounding_errors(stations)

    # Optionally pickle and save
    if pickle:
        logging.info("Pickling")
        save_object(stations, 'stations.pkl')

    # Check if QC is to be performed
    if control.qc_flag:
        stations = qc_main.qc(stations,err_file)
        # Take off the start and end times from the arrays
        remove_time_buffer(stations)

    # Sort stations by station name
    stations = OrderedDict(sorted(stations.items()))

    # Create Output filename
    filename = output

    dimensions = cfg.read_dimensions()
    num_stations = dimensions['nstations']
    time_dim = dimensions['time']

    # Format each observation into a 2D array with
    # dimensions of # of stations and # of times
    if pickle:
        logging.info("Pickling")
        save_object(stations, 'postqc.pkl')
    logging.info("Construct 2D observation arrays")
    camps_data = []
    example_station = list(stations.values())[0]
    obs = list(example_station.observations.keys())
    obs.remove('TIME')
    start_time = dates[0]
    end_time = dates[-1]
    logging.info("start time: " + start_time)
    logging.info("end time:   " + end_time)

    met_to_nc = cfg.read_metar_nc_lookup()
    for metar_name in obs:
        # Set the observation name to the standard CAMPS name
        try:
            observation_name = met_to_nc[metar_name]
        except:
            logging.error("Cannot find the netcdf equivalent of " +
                          metar_name +
                          "in METAR lookup table. Skipping.")
            continue

        # Loop through the stations and stitch together the current observation
        temp_obs = []
        for station_name, cur_station in stations.items():
            if 'latitude' in observation_name:
                temp_obs.append(list(np.repeat(stn_tbl[station_name]['lat'],len(dates))))
            elif 'longitude' in observation_name:
                temp_obs.append(list(np.repeat(stn_tbl[station_name]['lon'],len(dates))))
            else:
                temp_obs.append(cur_station.get_obs(metar_name))
        obs_data = np.array(temp_obs)
        logging.info(observation_name)

        # Construct Camps data object
        camps_obj = Camps_data(observation_name)
        try:
            camps_obj.metadata['vertical_coord'] = camps_obj.metadata.pop('coordinates')
        except:
            pass
        if camps_obj.is_feature_of_interest() and len(obs_data.shape)>1:
            obs_data = obs_data[:,0]
            camps_obj.set_dimensions((num_stations,))
        else:
            camps_obj.set_dimensions((time_dim,num_stations))
        camps_obj.add_data(obs_data)
        camps_obj.add_source('METAR')
        camps_obj.add_process('DecodeBUFR')
        if qc_flag: camps_obj.add_process('METARQC')
        camps_obj.change_data_type()

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

    camps_obj = pack_station_names(list(stations.keys()))
    camps_obj.add_source('METAR')
    camps_data.append(camps_obj)

    if qc_flag:
        extra_globals = {"source": "Data from METAR with MDL Quality Control"}
    else:
        extra_globals = {"source": "Data from METAR (No MDL Quality Control)"}

    # TEMPORARY: Need to perform 2 actions here. We should do this elsewhere, but here for now...
    #
    # 1) Unscale precip obs. Precip obs in MDL hourly table are units of hundreths of inches
    #    (i.e. 1.00 inches is 100).
    # 2) Trace amounts in the MDL hourly table are coded as -4.  Here we need to set these
    #    to a "defined" trace amount as float of value 0.004.
    for c in camps_data:
        if "precipitation_amount" in c.standard_name:
            c.data = np.where(np.logical_and(c.data>=0.0,c.data<9999.),c.data/100.0,c.data)
            c.data = np.where(c.data==-4,np.float32(0.004),c.data)
    # TEMPORARY

    # Write into netCDF4 file
    writer.write(camps_data, filename, extra_globals)
    if log_file:
        out_log.close()


def check_num_procs(num_procs):
    """Returns the minimum of the requested number of processors
    and the available number of processors.
    """

    max_cpu_count = multiprocessing.cpu_count()
    if num_procs > max_cpu_count:
        logging.warning("More processors specified than available")
        logging.warning(
            "defaulting to number of processors available: " + max_cpu_count)
        return max_cpu_count

    return num_procs


def add_time(start, end, stride=None, time_bounds=None):
    """Create and return PhenomenonTime objects, if observation is instantaneous,
    or PhenomenonTimePeriod objects, if observation applies over a period of time."""

    time = []
    if stride is None:
        stride = Time.ONE_HOUR

    if time_bounds:
        pt = Time.PhenomenonTimePeriod(start_time=start, end_time=end, stride=stride, period=time_bounds)
    else:
        pt = Time.PhenomenonTime(start_time=start, end_time=end, stride=stride)
    time.append(pt)

    return time


def pack_station_names(names):
    """Constructs and returns Camps data object for stations."""

    w_obj = Camps_data('stations')
    max_chars = max([len(i) for i in names])
    names = [name + ('_' * (max_chars - len(name))) for name in names]
    station_name_arr = np.array([])
    if len(names) == 1:
        char_arr = np.array(list(names[0]))
        station_name_arr = np.reshape(char_arr,(len(char_arr.shape),char_arr.shape[0]))
    elif len(names) > 1:
        station_name_arr = np.array(names)
    w_obj.set_dimensions(tuple(['stations']))
    w_obj.add_data(station_name_arr)
    w_obj.add_metadata("fill_value", '_')

    return w_obj


if __name__ == '__main__':
    main()
