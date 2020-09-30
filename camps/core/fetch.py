import sys
import os
import glob
import copy
import pdb
import logging
from netCDF4 import Dataset
from datetime import timedelta
from datetime import datetime
from os.path import basename

from ..registry.db import db as db
from ..registry import util as cfg
from . import reader as reader
from . import Time

"""Module: fetch.py
Fetches the data and metadata of a specified variable that is
stored in a netCDF file and returns it as a camps data object.

Methods:
    fetch
    get_record_filename
    get_matching_id
    has_matching_id
    get_id
    fetch_many_dates
    find_date
    printdict
"""


def fetch(filepaths, time=None, lead_time=None, repeat=False, ids=None, **metadata_dict):
    """Given a properly formated metadata dictionary, finds the variable amongst
    the files. If the Observed property is recognized as a variable that needs
    to be computed, then a routine will be called to compute the variable.


    Args:
        filepaths (list): list of filepaths to variable data.
        time (optional, int): Number of seconds after epoch.
        lead_time (optional, int): Number of seconds after forecast run time.
        **metadata_dict (dict): Metadata matching desired variable.
        Formatted::
            {
                'property'        : str
                'source'          : str
                'start'           : int
                'end'             : int
                'duration'        : int
                'duration_method' : str
                'vert_coord1'     : int
                'vert_coord2'     : int
                'vert_method'     : str
                'vert_units'      : str
                'file_id'         : int
                'forecast_period' : int
            }

    Returns:
        If successful, returns Camps_data object read from NetCDF.
        Otherwise, returns None if no variables are found.

    Raises:
        RuntimeError: If multiple variables are found matching provided metadata."""


    if time is not None and type(time) is datetime:
        time = Time.epoch_time(time)
    # Get a start and end range
    if 'start' not in list(metadata_dict.keys()) and 'end' not in list(metadata_dict.keys()) and time is not None:
        start=None
        end=None
        if time is not None:
            start = time
            end = time
        if lead_time is not None:
            end += lead_time*3600

        metadata_dict['start'] = start
        metadata_dict['end'] = end
    # If multiple input file ids are given, need to check for
    # the desired variable in all files. Loop over files
    # until found.
    if isinstance(ids,list):
        file_id = None
        i = 0
        while file_id is not ids[-1]:
            file_id = ids[i]
            i += 1
            metadata_dict['file_id'] = file_id
            prop = metadata_dict['property']
            ret = db.get_variable(**metadata_dict)
            if len(ret)>0:
                break
            if file_id==ids[-1] and prop!=basename(prop):
                metadata_dict['property'] = basename(prop)
                file_id = None
                i = 0
    elif ids is None:
        ret = db.get_variable(**metadata_dict)
    # Check if calling the database gives any entries.
    num_records_returned = len(ret)
    logging.debug('Number of records returned:' + str(num_records_returned))
    if num_records_returned > 1:
        if repeat == False:
            # Catch this error...what error should be thrown? We shouldn't have
            # multiple returns unless intentional.
            raise
        # If we are expecting multiple returns ojs...
        # Loop through ret and return an array of the objets so we can get all the durations...
        elif repeat == True:
            var_list = []
            for r in ret:
                record = r
                log_str = "Found one of %s Matching record." %(str(len(ret)))
                logging.info(log_str)
                filepath = get_matching_id(filepaths,record['file_id'])
                nc_variable_name = record['name']
                if 'reserved1' not in metadata_dict: #reserved1 should really always be set to either 'grid' or 'vector'
                    logging.warning("reserved1 is missing from  metadata_dict")
                else:
                    if metadata_dict['reserved1'] == 'vector': #if data is vector then we can't subset from lead_time
                        lead_time = None
                variable = reader.read_var(filepath, nc_variable_name, lead_time, time)
                if variable is not None:
                    variable.add_metadata('filepath',filepath)
                var_list.append(variable)
            return var_list

    elif num_records_returned == 0:
        # Check if another fetch without start and end might yield a variable
        # If a variable is returned. Compare returned start and end times to
        # initial search parameters and determine if desired time is invalid.
        search_dict = copy.copy(metadata_dict)
        start = search_dict.pop('start')
        end = search_dict.pop('end')
        ret = db.get_variable(**search_dict)
        if len(ret) == 0:
            pass
        elif len(ret)==1:
            var_start = ret[0]['start']
            var_end = ret[0]['end']
            if start < var_start or end > var_end or start > var_end or end < var_start:
                logging.error("Fetch for "+metadata_dict['property']+" with start: "+str(start)+
                              " and end: "+str(end)+" failed. Outside of valid times for variable.")
                raise AssertionError("Start time: "+str(start)+" and End time: "+str(end)+" could not be found within valid times for variable in input files")
        elif len(ret)>1:
            logging.error("Number of returned variables is: "+str(len(ret))+". Too many returned variables.")
            raise ValueError
        # Check if another fetch without full URI might yield results
        if 'property' in metadata_dict:
            prop = metadata_dict['property']
            prop_basename = basename(prop)
            if prop != prop_basename:
                metadata_dict['property'] = prop_basename
                return fetch(filepaths, time=time,lead_time=lead_time,**metadata_dict)
        # Otherwise return that nothing was found
        logging.warning("Variable "+metadata_dict['property']+" not found. Returning None.")
        return None
    elif num_records_returned == 1:
        record = ret[0]
        log_str = "Found one Matching record."
        logging.info(log_str)
        filepath = get_matching_id(filepaths,record['file_id'])
        nc_variable_name = record['name']
        if 'reserved1' not in metadata_dict: #reserved1 should really always be set to either 'grid' or 'vector'
            logging.warning("reserved1 is missing from  metatdata_dict")
        else:
            if metadata_dict['reserved1'] == 'vector': #if data is vector then we can't subset from lead_time
                lead_time = None
        variable = reader.read_var(filepath, nc_variable_name, lead_time, time)
        if variable is not None:
            variable.add_metadata('filepath',filepath)
        return variable

def get_matching_id(files, id):
    """Return absolute path if id matches a netcdf file in list of files."""
    for file in files:
        if has_matching_id(file, id):
            return file


def has_matching_id(file, id):
    """Returns true if file has the the proper ID"""
    nc = Dataset(file, mode='r')
    check_id = -1 # initialize
    try:
        check_id = nc.getncattr('file_id')
    except:
        logging.warning("File: '" +file+ "' has no file_id global attr.")
        return False
    nc.close()
    return check_id == id

def get_id(file):
    """Returns a file_id or None"""

    try:
        nc = Dataset(file, mode='r')
        try:
            file_id = str(nc.getncattr('file_id'))
        except:
            logging.warning("File: '" +file+ "' has no file_id global attr.")
            nc.close()
            return None
    except Exception as msg:
        logging.warning(str(msg))
        return None
    nc.close()
    return file_id

def fetch_many_dates(filepaths, start, end, stride, metadata_dict, lead_time=None,ids=None):
    """Fetch a variable over more than one date.
    """
    # Create a date iterator.
    cur = copy.copy(start)
    all_data = []
    while cur <= end:
        # fetch data
        if ids is None:
            var = fetch(filepaths, Time.epoch_time(cur), lead_time=lead_time, **metadata_dict)
        elif isinstance(ids,list):
            var = fetch(filepaths, Time.epoch_time(cur), lead_time=lead_time,ids=ids, **metadata_dict)
        all_data.append(var)
        cur += stride
    return all_data


#def printdict(dict):
#    for k,v in dict.iteritems():
#        print(str(k) + " : " + str(v))
