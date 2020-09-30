import numpy as np
from .nc_writable import nc_writable
import netCDF4
import pdb

class Location(nc_writable):
    """Class holding location data.  Includes location information such
    as latitude, longitude, x, y, and station names.
    """

    station = None


    def __init__(self, *args):
        """Initializes location to the arguments.

        Args:
            args (list): untyped location data.
                May be arrays, dicts, or netcdf variable objects
        """

        self.location_data = args


    def write_to_nc(self, nc_handle):
        """Writes object's netCDF representation as a
            netCDF Variable to the nc_handle.

        Args:
            nc_handle (:obj:netCDF4.Dataset): netCDF4 filehandle object.
        """

        for i in location_data:
            write_to_nc(i)


    def get_x(self):
        """Get's the x coordinate of projection from location_data.

        Returns:
            (numpy.array): x coordinate of projection.
        """

        for i in self.location_data:
            if i.name == 'x':
                return i[:]


    def get_y(self):
        """Get's the y coordinate of projection from location_data.

        Returns:
            (numpy.array): y coordinate of projection.
        """

        for i in self.location_data:
            if i.name == 'y':
                return i[:]


    def set_stations(self, data):
        """Sets the object's station data

        Args:
            data (np.ndarray): data holding station names.
        """

        self.station = data


    def get_stations(self):
        """Gets the objects stations.

        Returns:
            (list): list of strings representing the station names.
        """

        if self.station is not None:
            return self.station

        for i in self.location_data:
            if i.name == 'station':
                if isinstance(i[:][0][0], str):
                    return netCDF4.chartostring(i[:].astype('S1'))
                else:
                    return netCDF4.chartostring(i[:])
