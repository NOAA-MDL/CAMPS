import abc
from netCDF4 import Dataset

"""Interface ensuring there is a method to produce a netCDF4 Variable object.
"""
ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})

class nc_writable(ABC):

    @abc.abstractmethod
    def write_to_nc(self, nc_handle):
        """Abstract method to write a netCDF Variable to the nc_handle

        Args:
            nc_handle (netCDF4.Dataset): netCDF4 filehandle object
        """
        pass
