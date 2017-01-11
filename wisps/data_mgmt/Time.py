import numpy as np
from datetime import datetime
from datetime import timedelta
from nc_writable import nc_writable

class Time(nc_writable):

    def __init__(self, start_time, end_time):
        """
        Initializes the valid_time, observation_time, phenomenon_time,
        and lead time arrays.
        """
        self.valid_time = np.array([]) # Time at which observation is still valid
        self.observation_time = np.array([]) 
        self.phenomenon_time = np.array([])
        self.lead_time = np.array([])
        self.dimension = self.get_dimension_name()

    def get_nc_variable(self, nc_handle):
        """
        Adds the netCDF Variable representation of the Time.
        """
        self.write_observation_time(nc_handle)
        self.write_phenomenon_time(nc_handle)
        self.write_valid_time(nc_handle)
        self.write_lead_time(nc_handle)
        self.write_time_bouds(nc_handle)
           
    def write_observation_time(self,nc_handle):
        """Create Observation Time Variable """
        nc_var = nc_handle.createVariable(
                'observation_time', 
                int,
                dimensions=(self.dimension))
        nc_var[:] = self.observation_time
        self.add_common_metadata(nc_var)

    def write_phenomenon_time(self,nc_handle):
        """Create Phenomenon Time Variable """
        nc_var = nc_handle.createVariable(
                'phenomenon_time',
                int,
                dimensions=(self.dimension))
        nc_var[:] = self.phenomenon_time
        self.add_common_metadata(nc_var)

    def write_valid_time(self,nc_handle):
        """ Create Valid Time Variable """

        nc_valid_time = nc_handle.createVariable(
                'valid_time',                # Variable name
                int,                         # dtype
                dimensions=(self.dimension)) # Dimension names
        nc_valid_time[:] = self.valid_time
        self.add_common_metadata(nc_valid_time)

    def write_lead_time(self,nc_handle):
        """Write Lead Time Variable if exists"""

        if len(lead_time > 0):
            nc_var = nc_handle.createVariable(
                    'lead_time',
                    int, 
                    dimensions=(self.dimension))
            nc_var[:] = self.lead_time
            self.add_common_metadata(nc_var)

    def write_time_bounds(self,nc_handle):
        # Write Time Bounds Variable if exists
        try :
            nc_var = nc_handle.createVariable('time_bounds', int)
            nc_var[:] = self.bounds
            self.add_common_metadata(nc_var)
        except NameError:
            print 'No time bounds'

    def add_common_metadata(self, nc_var):
        """
        Adds metadata that is common to Time variables.
        """
        setattr(nc_var, 'calendar', 'gregorian')
        setattr(nc_var, 'units', 'seconds')

    def get_dimension_name(self):
        """ Provides a way accessing the name of the time dimension """
        return 'time'
    
    def add_bounds(self, stride, offset):
        """
        adds a bounds array to the object, where stride is 
        the number of time steps to skip, and offset is the
        starting point in the array
        """
#        size = (len(self.observation_time) - offset) / stride
        bounds = []
        for i in range(offset, len(self.observation_time), stride):
            self.bounds.append(self.observation_time[i])
        self.bounds = np.array(self.bounds)
        return self.bounds

def parse_ISO_standard_time(time):
        """
        Given a string that is the ISO standard representation of time,
        Return a the epoch time.
        """
        pass

def parse_development_sample(sample_str):
    """
    Given a string with an ISO interval representation, 
    such as 2014-04-01/2014-09-30, returns tuple of 2 datetimes 
    where index 0 = the start date, and index 1 = the end date
    """
    start,end = sample_string.split("/")
    dt_start = datetime(year=start[:4], month=start[5:7], day=start[8:])
    dt_end = datetime(year=end[:4], month=end[5:7], day=end[8:])
    return (dt_start, dt_end)

def parse_forecast_reference_time(forecast_str):
    """
    Given a string of type YYYY-MM-DDTFF,
    returns the FF component, which represents the
    forcast reference time, as a tuple. Where 
    index 0 = number of hours
    index 1 = number of seconds, and 
    """
    hour = forecast_str[11:]
    hour = int(hour)
    seconds = hour * 60 * 60
    return (hour, seconds)
         
