import numpy as np
from nc_writable import nc_writable


class Location(nc_writable):
    """Class to hold location data. Includes latitude and longitude array,
    as well as the station names
    """

    def __init__(self, *args):
        """Initializes empy latitude, longitude, and station arrays
        """
        self.location_data = args

    def write_to_nc(self, nc_handle):
        """Writes this objects netCDF representation as a
        netCDF Variable to the nc_handle.
        """
        for i in location_data:
            write_to_nc(i)
    
    def get_x(self):
        """
        """
        for i in self.location_data:
            if i.name == 'x':
                return i[:]

    def get_y(self):
        """
        """
        for i in self.location_data:
            if i.name == 'y':
                return i[:]




