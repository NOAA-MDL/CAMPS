import os
import sys
import time
import pdb
import numpy as np
import logging
import random
import uuid
from netCDF4 import Dataset

from ..registry.db import db as db
from ..registry import util as util
from Camps_data import Camps_data

"""
Module to handle writing Camps netCDF data
"""


def write(camps_data, filename, global_attrs={}, overwrite=True,
          write_to_db=True):
    """Writes a list of Camps_data to NetCDF file.
    camps_data is expected to be a list of Camps_data objects.
    filename is the filename to write to.
    global_attrs are additional global attributes to add to the file.
    overwite specifies whether a file should new or appended to.

    Args:
        camps_data (:obj:`list` of :obj:`Camps_data` or :obj:`Camps_data`):
            Camps_data or list of Camps_data objects to be written to NetCDF file.
        filename (str): NetCDF filename.
        global_attrs (dict): Dict of global attributes for NetCDF file.
        overwrite (bool): If true, write a new file regardless of whether a file
            already exists, otherwise append to existing file if possible.
        write_to_db (bool): write to database

    Returns:
        True if successful, False otherwise.
    """

    logging.info("\nWriting to "+filename+"\n")
    file_id = str(uuid.uuid4())
    global_attrs['file_id'] = file_id

    if type(camps_data) is not list:
        camps_data = [camps_data]

    start_time = time.time()

    if overwrite:
        mode = 'w'
    else:
        mode = 'a'
    nc = Dataset(filename, mode=mode, format="NETCDF4")

    #----------------------------------------------------------------------
    #I don't understand what this is for...if it errors out it just skips.
    #----------------------------------------------------------------------
    #Get all dimenesions in the list.
    #Will error out if dimensions arn't correct.
    try:
        dims = get_dimensions(camps_data)
        #Write dimensions
        for d_name, size in dims.iteritems():
            nc.createDimension(d_name, size)
    except:
        pass
    #-----------------------------------------------------------------------

    #Write the data by calling its write_to_nc function
    primary_vars = []
    #write file info to the file_info table if write_to_db is true
    if write_to_db:
        db.insert_file_info(filename,str(file_id))
        #what if add_to_database fails...need some kind of check
        #what if it fails for only some predictors but not others?

    for da in camps_data:
        name = da.write_to_nc(nc)
        primary_vars.append(name)
        if write_to_db:
            try:
                da.add_to_database(filename, file_id)
            except AttributeError as e :
                logging.info(e)
            #pass # Variable doesn't have a Phenomenon Time.

    #global_attrs['primary_variables'] = get_primary_variables(camps_data)
    global_attrs['primary_variables'] = ' '.join(primary_vars)
    write_global_attributes(nc, global_attrs)
    write_prefixes(nc)
    nc.close()

    end_time = time.time()
    elapsed_time = end_time - start_time
    logging.debug("elapsed time to write variables:" + str(elapsed_time))
    logging.debug("approximately " +
                  str(elapsed_time / len(camps_data)) +
                  " seconds per variable")
    logging.info("writing complete. Closing nc file: "+filename)


def get_primary_variables(w_list):
    """Return space-separated primary variables.

    Args:
        w_list (:obj:`list` of :obj:Camps_data): variables that will have
                their names extracted.

    Returns:
        str: Space-separated string of variable names

    """

    PV_str = ""
    for w in w_list:
        PV_str += " " + w.get_variable_name()

    return PV_str


def write_prefixes(nc):
    """Writes the prefixes defined in netcdf.yaml.
    prefixes are written as their own group.
    Also may add additional information.

    Args:
        nc (:obj:`Dataset`): NetCDF file handle.

    Returns:
        None
    """

    prefixes = util.read_prefixes()
    group = nc.createGroup('prefix_list')
    for name, value in prefixes.iteritems():
        setattr(group, name, value)


def write_global_attributes(nc, extra_globals):
    """Writes the global attributes as defined in netcdf.yaml.
    Also may add additional information.

    Args:
        nc (:obj:`Dataset`): NetCDF file handle.
        extra_globals(dict): Additional global attributes to be added to `nc`

    Returns:
        None
    """

    nc_globals = util.read_globals()
    nc_globals.update(extra_globals)
    for name, value in nc_globals.iteritems():
        setattr(nc, name, value)


def get_dimensions(camps_data):
    """Checks if each object's dimensions have the same length.
    Confirms shape of data is same number of dimensions.

    Args:
        w_obj (:obj:list of :obj:`Camps_data`): To assure dimensions are consistent.

    Returns:
        A dictionary where the key is the dimension name
        and the value is the number of elements.
    """

    # Define count; where the
    # key is the dimension name, and the
    # value is the shape of the data.
    count = {}
    for i in camps_data:

        dims = i.dimensions
        shape = i.data.shape
        if i.data.size > 0 and len(dims) != len(shape):
            logging.error(
                "The shape of data and number of dimensions dont match")
            logging.error("The Problem is with, " + i.name)
            logging.error("dimensions : " + str(dims))
            logging.error("shape      : " + str(shape))
            raise ValueError

        for c, d in enumerate(dims):
            if d not in count:
                count[d] = shape[c]
            elif count[d] != shape[c]:
                logging.warning("Dimension " + d + " is not consistant " +
                                "with other dimensions in list")
                raise ValueError

    return count


def write_stations(nc, station_list):
    """Writes station names as a variable in netcdf filehandle.

    Args:
        nc (:obj:netCDF4.Dataset): netCDF4 filehandle.
        station_list (list of strings) List of strings that represents stations
    """

    dim_name = util.read_dimensions()['nstations']
    max_number_of_chars = len(max(station_list))
    nc.createDimension('number_of_characters', max_number_of_chars)
    call_var = nc.createVariable('station','c', (dim_name, 'number_of_characters'))
    setattr(call_var, 'standard_name', 'platform_id')
    setattr(call_var, 'long_name', 'observation station name')
    station_name_arr = []
    for station_name in station_list:
        char_arr = np.array(list(station_name), 'c')
        if len(station_name_arr) == 0:
            station_name_arr = char_arr
        else:
            station_name_arr = np.vstack((station_name_arr, char_arr))
    call_var[:] = station_name_arr
