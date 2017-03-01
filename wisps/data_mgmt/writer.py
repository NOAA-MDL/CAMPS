import os,sys
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
import registry.db.db as db
import registry.util as util

from netCDF4 import Dataset
from Wisps_data import Wisps_data
import time
import pdb


"""
Module to handle writing Wisps netCDF data
"""


def open_nc(filename):
    """
    Opens a netCDF file for writing and returns a Dataset object
    """
    nc = Dataset(filename, mode='w', format="NETCDF4")
    return nc

def write(wisps_data, filename, global_attrs={}):
    """
    Writes a list of Wisps_data to NetCDF file
    """
    print "\nWriting\n"
    start_time = time.time()
    # Get all dimenesions in the list.
    # Will error out if dimensions arn't correct.
    nc = open_nc(filename)
    try:
        dims = get_dimensions(wisps_data)
        # Write dimensions
        for d_name,size in dims.iteritems():
            nc.createDimension(d_name, size)
    except:
        pass

    # Write the data by calling its write_to_nc function
    for d in wisps_data:
        d.write_to_nc(nc)
    write_global_attributes(nc, global_attrs)
    nc.close()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print "elapsed time to write variables:", elapsed_time
    print "approximately", elapsed_time/len(wisps_data), "seconds per variable"

def write_global_attributes(nc, extra_globals):
    """Writes the global attributes as defined in netcdf.yml . 
    Additionally, it adds time specific information. 
    """
    nc_globals = util.read_globals()
    nc_globals.update(extra_globals)
    for name,value in nc_globals.iteritems():
        setattr(nc, name, value)

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
            print "Problem: shape of data and number of dimensions dont match"
            print "Problem: with,",i.name
            raise ValueError
        for c,d in enumerate(dims):
            if d not in count:
                count[d] = shape[c]
            elif count[d] != shape[c]:
                print "Problem: dimension", d, "is not consistant with other " \
                        "dimensions in list"
                raise ValueError
    return count

