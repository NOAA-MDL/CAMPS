import os
import sys
import time
import pdb
import logging
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
import registry.db.db as db
import registry.util as util
from netCDF4 import Dataset
from Wisps_data import Wisps_data

"""
Module to handle writing Wisps netCDF data
"""


def write(wisps_data, filename, global_attrs={}, overwrite=True,
          write_to_db=True):
    """
    Writes a list of Wisps_data to NetCDF file.
    wisps_data is expected to be a list of Wisps_data objects.
    filename is the filename to write to.
    global_attrs are additional global attributes to add to the file.
    overwite specifies whether a file should new or appended to.
    """
    logging.info("\nWriting to "+filename+"\n")
    if type(wisps_data) is not list:
        wisps_data = list(wisps_data)
    start_time = time.time()
    if overwrite:
        mode = 'w'
    else:
        mode = 'a'
    nc = Dataset(filename, mode=mode, format="NETCDF4")
    # Get all dimenesions in the list.
    # Will error out if dimensions arn't correct.
    try:
        dims = get_dimensions(wisps_data)
        # Write dimensions
        for d_name, size in dims.iteritems():
            nc.createDimension(d_name, size)
    except:
        pass
    # Write the data by calling its write_to_nc function
    primary_vars = []
    for d in wisps_data:
        name = d.write_to_nc(nc)
        primary_vars.append(name)
        try:
            d.add_to_database(filename)
        except AttributeError:
            pass # Variable doesn't have a Phenomenon Time.
    #global_attrs['primary_variables'] = get_primary_variables(wisps_data)
    global_attrs['primary_variables'] = ' '.join(primary_vars)
    write_global_attributes(nc, global_attrs)
    nc.close()

    end_time = time.time()
    elapsed_time = end_time - start_time
    logging.debug("elapsed time to write variables:" + str(elapsed_time))
    logging.debug("approximately " +
                  str(elapsed_time / len(wisps_data)) +
                  " seconds per variable")
    logging.info("writing complete. Closing nc file: "+filename)


def get_primary_variables(w_list):
    """Return space-separated primary variables.
    """
    PV_str = ""
    for w in w_list:
        PV_str += " " + w.get_variable_name()
    return PV_str


def write_global_attributes(nc, extra_globals):
    """Writes the global attributes as defined in netcdf.yml.
    Also may add additional information.
    """
    nc_globals = util.read_globals()
    nc_globals.update(extra_globals)
    for name, value in nc_globals.iteritems():
        setattr(nc, name, value)


def update_variable_db(w_obj):
    """Adds a new entry to the variable database
    """
    db.insert_variable(
        property,
        source,
        leadtime,
        start,
        end,
        duration,
        duration_method,
        vert_coord1,
        vert_coord2,
        vert_method,
        filename)


def get_dimensions(wisps_data):
    """
    Checks if each object's dimensions have the same length.
    Confirms shape of data is same number of dimensions.
    returns a dictionary where the key is the dimension name
    and the value is the number of elements.
    """
    # Define count; where the
    # key is the dimension name, and the
    # value is the shape of the data.
    count = {}
    for i in wisps_data:
        dims = i.dimensions
        shape = i.data.shape
        if len(dims) != len(shape):
            logging.error(
                "Problem: shape of data and number of dimensions dont match")
            logging.error("Problem: with, " + i.name)
            raise ValueError
        for c, d in enumerate(dims):
            if d not in count:
                count[d] = shape[c]
            elif count[d] != shape[c]:
                logging.warning("Dimension " + d + " is not consistant " +
                                "with other dimensions in list")
                raise ValueError
    return count
