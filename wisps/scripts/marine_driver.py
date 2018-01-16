#!/usr/bin/env python
# Add a relative path
import sys
import os
import time
import numpy as np
import logging
from netCDF4 import Dataset
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
from data_mgmt.Wisps_data import Wisps_data
import data_mgmt.Time as Time
import data_mgmt.writer as writer
from datetime import datetime, timedelta
from marine_to_nc.marinereader import marinereader
import registry.util as cfg
import registry.db.db as db


def main(control_file=None):
    """
    Main function for converting marine CSV file to WISPS netCED file
    """
    # Read Control
    if control_file:
        control = cfg.read_yaml(control_file)
    else:
        control = cfg.read_marine_control()
    in_dir = control['input_directory']
    in_file = control['input_filename']
    out_dir = control['output_directory']
    out_file = control['output_filename']
    start_date = control['start_date']
    end_date = control['end_date']
    log_file = control['log_file']
    debug_level = control['debug_level']

    if log_file:
        out_log = open(log_file, 'w')
        sys.stdout = out_log
        sys.stderr = out_log
    try:
        logging.getLogger('').handlers = []
        level = logging.getLevelName(debug_level)
        logging.basicConfig(level=level)
    except:
        print "Logging setup failed"
        raise

    in_path = in_dir + in_file
    out_path = out_dir + out_file + '.nc'

    # Read Configuration
    marine_convert = cfg.read_marine_lookup()
    nc_vars = cfg.read_variables()

    # Read file
    print "Reading marine file"
    reader = marinereader(in_path)
    if start_date:
        reader.read(start_date=start_date, end_date=end_date)
    reader.read(end_date=end_date)

    # Stack the stations to make 3d array
    multi_d = []
    for name, observations in reader.station_list.iteritems():
        reader.station_list[name] = np.array(observations)
        multi_d = multi_d + [reader.station_list[name]]

    # Package data into Wisps_data object. Write data
    observations = reader.observations
    multi_d = np.array(multi_d)
    station_names = reader.station_list.keys()
    obj_list = []
    for i, observation_name in enumerate(observations):
        ob_arr = multi_d[:, :, i]
        std_name = marine_convert[observation_name]
        try:
            std_var = nc_vars[std_name]
            obj = Wisps_data(std_name)
            ob_arr = ob_arr.astype(std_var['data_type'])
            obj.set_dimensions(tuple(std_var['dimensions']))
            times = get_time(reader.dates)
            obj.time = times
            obj.add_data(ob_arr)
            obj.add_process('MarineObProcStep1')
            obj.add_process('MarineObProcStep2')
            obj_list.append(obj)
        except KeyError:
            print observation_name, "undefined"

    obj_list = add_marine_procedures(obj_list)

    obj = pack_station_names(station_names)
    obj.time = get_time(reader.dates)
    #obj.add_source("MARINE")
    obj_list.append(obj)


    writer.write(obj_list, out_path)
    if log_file:
        out_log.close()

def add_marine_procedures(obj_list):
    """Add Marine QC procedures"""
    for obj in obj_list:
        obj.add_process('MarineObProcStep1')
    return obj_list

def get_time(dates):
    """Returns phenom time from list of dates"""
    start_date = dates[0]
    end_date = dates[-1]
    return [
            Time.PhenomenonTime(start_time=start_date, end_time=end_date),
            Time.ResultTime(start_time=start_date, end_time=end_date),
            # Valid Time will be forever
            Time.ValidTime(start_time=start_date, end_time=end_date)
            ]


def pack_station_names(names):
    w_obj = Wisps_data('station')

    station_name_arr = np.array([])
    for name in names:
        char_arr = np.array(list(name), 'c')
        if len(station_name_arr) == 0:
            station_name_arr = char_arr
        else:
            station_name_arr = np.vstack((station_name_arr, char_arr))
    w_obj.set_dimensions(tuple(['number_of_stations', 'num_characters']))
    w_obj.add_data(station_name_arr)
    return w_obj


if __name__ == "__main__":
    try:
        main(control_file=sys.argv[1])
    except IndexError:
        main()
