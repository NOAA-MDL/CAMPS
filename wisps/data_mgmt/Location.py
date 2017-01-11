import numpy as np
from nc_writable import nc_writable 

class Location(nc_writable):
    """
    Class to hold location data. Includes latitude and longitude array, 
    as well as the station names
    """
    def __init__(self):
        """
        Initializes empy latitude, longitude, and station arrays
        """
        self.lat = np.array([])
        self.lon = np.array([])
        self.station_names = set([])

    def get_nc_variable(nc_handle):
        """
        Writes this objects netCDF representation as a 
        netCDF Variable to the nc_handle.
        """
        if len( self.station_names > 0 ):
            pass

    def num_stations(self):
        """
        Returns the number of stations.
        """
        return len(self.station_names)




