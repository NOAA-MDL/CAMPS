import os,sys
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
import registry.db.db as db

from netCDF4 import Dataset
from Wisps_data import Wisps_data
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

def write(wisps_data, filename):
    """
    Writes a list of Wisps_data to NetCDF file
    """
    # Get all dimenesions in the list.
    # Will error out if dimensions arn't correct.
    dims = get_dimensions(wisps_data)

    nc = open_nc(filename)

    # Write dimensions
    for d_name,size in dims.iteritems():
        nc.createDimension(d_name, size)

    # Write the data by calling its write_to_nc function
    for d in wisps_data:
        d.write_to_nc(nc)
    nc.close()

   
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
            raise ValueError
        for c,d in enumerate(dims):
            if d not in count:
                count[d] = shape[c]
            elif count[d] != shape[c]:
                print "Problem: dimension", d, "is not consisitant with other" \
                        "dimensions in list"
                raise ValueError
    return count

