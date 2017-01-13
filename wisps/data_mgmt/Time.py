import numpy as np
from datetime import datetime
from datetime import timedelta
from nc_writable import nc_writable

# Common amounts of time in seconds
ONE_MINUTE = 60
ONE_HOUR = ONE_MINUTE*60
ONE_DAY = ONE_HOUR*24

# Common time interpretation functions
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
    hours = forecast_str[11:]
    hours = int(hour)
    seconds = hour * ONE_HOUR
    return (hour, seconds)

def datetime_to_str(time):
    """
    Assumed that time is a datetime object.
    hours are represented YYYYMMDDHH
    """
    return str(time.year).zfill(4) + \
           str(time.month).zfill(2) + \
           str(time.day).zfill(2) + \
           str(time.hour).zfill(2)

def str_to_datetime(time):
    """
    Assumed that time is in form YYYYMMDDHH, which is the format of the
    self.hours array.
    """
    year = int(time[:4])
    month = int(time[4:6])
    day = int(time[6:8])
    hour =  int(time[8:10])
    return datetime(year,month,day,hour)

def epoch_to_datetime(seconds):
    """Converts epoch time to datetime"""
    return datetime.utcfromtimestamp(seconds)

def epoch_time(time):
    """Return hours array as seconds since the epoch """
    if type(time) is not datetime and type(time) is not str:
        raise TypeError("argument is not of type datetime or str")
    if type(time) is str:
        time = str_to_datetime(time)
    epoch = datetime.utcfromtimestamp(0)
    unix_time = lambda dt: (dt-epoch).total_seconds()
    seconds_since_epoch = unix_time(time)
    return seconds_since_epoch


class Time(nc_writable):
    """
    Baseclass representing time.
    """

    def __init__(self, start_time=None, end_time=None, stride=ONE_HOUR):
        """
        Initializes the valid_time, result_time, phenomenon_time,
        and lead time arrays.
        """
        self.data = np.array([])
        self.name = "time"
        if start_time and end_time:
            self.init_time_data(start_time, end_time, stride)
        
    def init_time_data(start_date, end_date, stride):
        """
        Fills the arrays with appropriate data.
        """
        # Type check
        if type(start_date) == str:
            start_date = str_to_datetime(start_date)
        if type(end_date) == str:
            end_date = str_to_datetime(end_date)
        if type(stride) == str:
            stride = int(str)
        if type(stride) is not timedelta:
            stride = timedelta(seconds=stride)
        
        # Create array with correct size
        size = num_timesteps(start_time, end_time, stride)
        self.data = np.zeros(size)
        
        # Initialize array with correct values
        cur_date = start_date
        for i in range(size):
            self.data[i] = epoch_time(cur_date)
            cur_date += stride

    def get_nc_variable(self, nc_handle):
        """
        Adds the netCDF Variable representation of the Time.
        """
        nc_time = nc_handle.createVariable(
                self.name,  
                int,                         
                dimensions=(self.dimension)) 
        nc_time[:] = self.name
        self.add_common_metadata(nc_valid_time)

    def num_timesteps(start_time, end_time, stride):
        """Calculates the number of timesteps between 
        a start and end time with a certain duration.
        """
        duration = end_time - start_time
        total_seconds = int(duration.total_seconds())
        timesteps = total_seconds / stride.total_seconds
        return timesteps

    def add_common_metadata(self, nc_var):
        """
        Adds metadata that is common to Time variables.
        """
        setattr(nc_var, 'calendar', 'gregorian')
        setattr(nc_var, 'units', 'seconds')

    def get_dimension_name(self):
        """ Provides a way accessing the name of the time dimension """
        return 'time'

    def __add__(self, other):
        if type(self) is type(other):
            self.data = np.append(self.data, other.data)
            return self
   

class PhenomenonTime(Time):
    """Class representing the Phenomenon Time
    Phenomenon time is colloquially, when the weather happens.
    It can be either an instant in time or 
    A period of time.
    """

    def __init__(self, start_time=None, end_time=None, stride=ONE_HOUR):
        """
        Initializes the data array
        """
        super(Time,self).__init__(start_time, end_time)       
        self.name = "OM_phenomenonTime"

class ValidTime(Time):
    """Class representing the valid time.
    The valid time is the time of intended use.
    Must be a period of time.
    """

    def __init__(self, start_time=None, end_time=None, stride=ONE_HOUR, valid_offset=0):
        """
        Initializes the data array.
        valid_offset can be:
        a function that is applied to the data array, 
        a deltatime duration, 
        a datetime fixed date, or 
        a 0 representing an unlimited valid time
        """
        super(Time,self).__init__(start_time, end_time, stride)       
        self.add_offset(valid_offset)

    def add_offset(self, offset):
        """Offset can be:
        a function that is applied to the data array, 
        a deltatime duration, 
        a datetime fixed date, or 
        a 0 representing an unlimited valid time
        """
        o_type = type(offset)
        a_function = callable(offset)

        if a_function:
            for i,value in enumerate(self.data):
                self.data[i] = offset(value)

        elif o_type is datetime:
            for i,value in enumerate(self.data):
                self.data[i] = epoch_time(offset)

        elif o_type is timedelta:
            for i,value in enumerate(self.data):
                self.data[i] += offset.total_seconds()
                
        elif o_type is int and offset == 0:
                self.data[i] = None


class ResultTime(Time):
    """Class representing the Result time.
    The result time is when the result (analysis, forcast)
    became available to data consumers.
    Must be an instant in time.
    """
    def __init__(self, start_time=None, end_time=None, stride=ONE_HOUR, result_time=None):
        """
        Initializes the data array
        """
        super(ResultTime,self).__init__(start_time, end_time)       
        self.name = 'OM_resultTime'
        self.append_result(result_time)
        
    def append_result(self, result_time):
        self.data[:] = result_time
        
    
class ForecastReferenceTime(Time):
    """Class representing the Forecast reference time.
    Where the Forecast Reference time is the 
    'data time', the time of the 
    analysis from which the forecast was
    made.
    """
    def __init__(self, start_time=None, end_time=None, stride=ONE_HOUR, reference_time=None):
        """
        Initializes the data array
        """
        super(ForecastReferenceTime,self).__init__(start_time, end_time)       
        self.name = 'forecast_reference_time'
        self.append_reference_time(reference_time)
        
    def append_reference_time(self, result_time):
        self.data[:] = result_time


class LeadTime(Time): 
    """Class representing the lead time.
    The lead_time Length of time (a duration) from 
    forecast_reference_time to the
    Phenomenon time
    """
    def __init__(self, forecast_ref_time, phenom_time):
        """
        Initializes the data array
        """
        self.name = "LeadTime"
        
        is_ref_time = type(forecast_ref_time) is ForecastReferenceTime
        is_phenom_time = type(phenom_tim) is PhenomenonTime
        if is_ref_time and is_phenom_time:
            self.data = phenom_time - forecast_ref_time




class BoundedTime(Time):
    """Class reproesenting the Bounded time. 
    The bounded time represents an instant in time 
    separated duration
    """
    
    def add_bounds(self, stride, offset):
        """
        adds a bounds array to the object, where stride is 
        the number of time steps to skip, and offset is the
        starting point in the array
        """
#        size = (len(self.result_time) - offset) / stride
        bounds = []
        for i in range(offset, len(self.result_time), stride):
            self.bounds.append(self.result_time[i])
        self.bounds = np.array(self.bounds)
        return self.bounds

         
