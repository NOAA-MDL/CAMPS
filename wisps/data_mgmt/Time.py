import sys
import os
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
import numpy as np
import registry.util as cfg
from datetime import datetime
from datetime import timedelta
from nc_writable import nc_writable
import re
import pdb

##
#class Time()
#class PhenomenonTime(Time)
#class ValidTime(Time)
#class ResultTime(Time)
#class ForecastReferenceTime(Time)
#class LeadTime(Time)
#class BoundedTime(Time)
##

# Common amounts of time in seconds
ONE_MINUTE = 60
ONE_HOUR = ONE_MINUTE*60
ONE_DAY = ONE_HOUR*24
FILL_VALUE = 9999

# Common time interpretation functions
def parse_ISO_standard_time(time):
    """Given a string that is the ISO standard representation of time,
    Return a the epoch time.
    """
    pass

def parse_development_sample(sample_str):
    """Given a string with an ISO interval representation, 
    such as 2014-04-01/2014-09-30, returns tuple of 2 datetimes 
    where index 0 = the start date, and index 1 = the end date
    """
    start,end = sample_string.split("/")
    dt_start = datetime(year=start[:4], month=start[5:7], day=start[8:])
    dt_end = datetime(year=end[:4], month=end[5:7], day=end[8:])
    return (dt_start, dt_end)

def parse_forecast_reference_time(forecast_str):
    """Given a string of type YYYY-MM-DDTFF,
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
    """Assumed that time is a datetime object.
    hours are represented YYYYMMDDHH
    """
    return str(time.year).zfill(4) + \
           str(time.month).zfill(2) + \
           str(time.day).zfill(2) + \
           str(time.hour).zfill(2)

def str_to_datetime(time):
    """Assumed that time is in form YYYYMMDDHH
    """
    year = int(time[:4])
    month = int(time[4:6])
    try:
        day = int(time[6:8])
    except:
        day = 1
    try:
        hour =  int(time[8:10])
    except:
        hour = 0
    return datetime(year,month,day,hour)

def epoch_to_datetime(seconds):
    """Converts epoch time to datetime"""
    return datetime.utcfromtimestamp(seconds)

def epoch_time(time):
    """Return hours array as seconds since the epoch,
    where time can be a datetime or str
    """
    if type(time) is not datetime and type(time) is not str:
        raise TypeError("argument is not of type datetime or str")
    if type(time) is str:
        time = str_to_datetime(time)
    epoch = datetime.utcfromtimestamp(0)
    unix_time = lambda dt: (dt-epoch).total_seconds()
    seconds_since_epoch = unix_time(time)
    # Remove the microsecond precision
    seconds_since_epoch = int(seconds_since_epoch)
    return seconds_since_epoch

def num_timesteps(start_time, end_time, stride=timedelta(hours=1)):
    """Calculates the number of timesteps between a start and end time with a certain duration.
    Assumes inclusive start and end times
    """
    duration = end_time - start_time
    total_seconds = int(duration.total_seconds())
    timesteps = int(total_seconds / stride.total_seconds())
    timesteps += 1 # To keep end time inclusive
    return timesteps 


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
    minute = 0
    if len(time) > 10:
        minute = int(time[10:12])
    return datetime(year,month,day,hour,minute)

def epoch_to_datetime(seconds):
    """Converts epoch time to datetime"""
    return datetime.utcfromtimestamp(seconds)

def epoch_time(time):
    """Return hours array as seconds since the epoch """
    if type(time) is not datetime and type(time) is not str and not np.string_:
        raise TypeError("argument is not of type datetime or str")
    if type(time) is str or type(time) is np.string_:
        time = str_to_datetime(time)
    epoch = datetime.utcfromtimestamp(0)
    unix_time = lambda dt: (dt-epoch).total_seconds()
    seconds_since_epoch = unix_time(time)
    return seconds_since_epoch


class Time(nc_writable):
    """Baseclass representing time.
    """

    def __init__(self, start_time=None, end_time=None, stride=ONE_HOUR):
        """Initializes the valid_time, result_time, phenomenon_time,
        and lead time arrays.
        """
        self.data = np.array([], dtype=int)
        self.metadata = {}
        try:
            self.metadata['wisps_role'] = self.name
        except:
            self.name = "time"
            self.metadata['wisps_role'] = self.name
        if start_time and end_time:
            self.init_time_data(start_time, end_time, stride)
        
    def init_time_data(self, start_date, end_date, stride):
        """Fills the arrays with appropriate data.
        start and end dates can be of type datetime,
        str (YYYYMMDD), or int (epoch time in seconds).
        end_time is non-inclusive.
        """
        # Type check
        if type(start_date) == str:
            start_date = str_to_datetime(start_date)
        elif type(start_date) == int:
            start_date = epoch_to_datetime(end_date)
        if type(end_date) == str:
            end_date = str_to_datetime(end_date)
        elif type(end_date) == int:
            end_date = epoch_to_datetime(end_date)
        if type(stride) == str:
            stride = int(str)
        elif type(stride) is not timedelta:
            stride = timedelta(seconds=stride)
        
        # Create array with correct size
        size = num_timesteps(start_date, end_date, stride)
        self.data = np.zeros(size)
        
        # Initialize array with correct values
        cur_date = start_date
        for i in range(size):
            self.data[i] = epoch_time(cur_date)
            cur_date += stride

    def write_to_nc(self, nc_handle):
        """Adds the netCDF Variable representation of the Time.
        If Time variable already exists, it will return None.
        Additional Time variables of same type will have consecutive 
        integers appended on the end of the variable name.
        """

        time_dim = self.get_dimension_name()
        if time_dim not in nc_handle.dimensions:
            if len(self.data.shape) == 2:
                nc_handle.createDimension(time_dim,len(self.data[1]))
            else:
                nc_handle.createDimension(time_dim,len(self.data))
        dim_tuple = (time_dim)

        if len(self.data.shape) == 2:
            bounded_dim = self.get_bounded_dimension_name()
            if bounded_dim not in nc_handle.dimensions:
                nc_handle.createDimension(bounded_dim, 2)
            dim_tuple = (bounded_dim,time_dim)
        else:
            alt_dim = self.check_dimensions(nc_handle)
            if alt_dim:
                time_dim = alt_dim
                dim_tuple = (time_dim)

        name,exists = self.get_name(nc_handle)
        if not exists:
            nc_time = nc_handle.createVariable(
                    name,  
                    int,                         
                    dimensions=dim_tuple,
                    fill_value=-FILL_VALUE) 
            nc_time[:] = self.data
            self.add_common_metadata(nc_time)
            # Add special Metadata
            for meta_name,value in self.metadata.iteritems():
                setattr(nc_time, meta_name, value)
        return name

    def get_name(self, nc_handle):
        """Looks for a match in Time variables.
        Returns a tuple containing the [0] - name of the variable
        and [1] - a boolean indicating if it already existed.
        """
        all_vars = nc_handle.variables
        varkeys = all_vars.keys()
        match = lambda var: re.match(r'^'+self.name+'\d*$',var,re.I)
        time_vars = filter(match,varkeys)
        for name in reversed(time_vars):
            var = all_vars[name]
            # Check for a data match
            if np.array_equal(var[:], self.data):
                return (name,True)
        if len(time_vars) == 0:
            name = self.name
        else:
            name = self.name + str(len(time_vars))
        return (name,False)

    def get_stride(self, as_timedelta=False):
        """Returns the number of seconds between two time steps.
        This function may provide misleading information if timesteps
        have an irregular step duration.
        """
        size = len(self.data)
        if size <= 1:
            raise IndexError("Time data has 1 or 0 elements")
        start = self.data[0]
        end = self.data[1]
        stride = end - start
        if as_timedelta:
            return timedelta(seconds=stride)
        return stride

        size = len(self.data)
        if size <= 1: 
            raise IndexError("Time.data.")
        start = self.data[9]

    def check_dimensions(self, nc_handle):
        """Check data dimension shape is equal to the nc handle dimension.
        """
        shape = self.data.shape
        time_dim = self.get_dimension_name()
        nc_dim_size = len(nc_handle.dimensions[time_dim])
        size = shape[0]
        if size != nc_dim_size: 
            # Find if one has already been created
            try: 
                count = 1
                while True:
                    alt_dim_name = time_dim + "_alt" + str(count)
                    count += 1
                    nc_dim_size = len(nc_handle.dimensions[alt_dim_name])
                    if size == nc_dim_size:
                        return alt_dim_name
                        break
            except KeyError:
                nc_handle.createDimension(alt_dim_name, size)
                return alt_dim_name

    def add_common_metadata(self, nc_var):
        """Adds metadata that is common to Time variables.
        """
        setattr(nc_var, 'calendar', 'gregorian')
        setattr(nc_var, 'units', 'seconds since 1970-01-01 00:00:00.0')

    def get_dimension_name(self):
        """Provides a way for accessing the name of the time dimension."""
        return cfg.read_dimensions()['time']

    def get_bounded_dimension_name(self):
        """Provides a way for accessing the name of the start and end 
        dimension.
        """
        return 'begin_end_size'

    def get_start_time(self):
        return epoch_to_datetime(int(self.data[0]))

    def get_end_time(self):
        return epoch_to_datetime(int(self.data[-1]))

    def __add__(self, other):
        """ overloading + opporator """
        if type(self) is type(other):
            self.data = np.append(self.data, other.data)
            return self

    def __str__(self):
        ret_str = self.name = "\n"
        if len(self.data > 0):
            ret_str += "start_time: "
            ret_str += str(epoch_to_datetime(self.data[0])) + "\n"
            ret_str += "end_time:   "
            ret_str += str(epoch_to_datetime(self.data[-1])) + "\n"
            ret_str += "Timesteps:  " 
            ret_str += str(len(self.data)) + "\n"
            ret_str += "Data: \n" 
            ret_str += "["+str(epoch_to_datetime(self.data[0])) + ", "
            ret_str += str(epoch_to_datetime(self.data[1])) + ",\n"
            ret_str += "  ....\n"
            ret_str += str(epoch_to_datetime(self.data[-2])) + ", "
            ret_str += str(epoch_to_datetime(self.data[-1])) + "]"

            return ret_str

    __repr__ = __str__

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        if self.data[0] == other.data[0]:
           if self.data[-1] == other.data[-1]:
                if len(self.data) == len(other.data):
                    return True
        return False

class PhenomenonTime(Time):
    """Class representing the Phenomenon Time
    Phenomenon time is colloquially, when the weather happens.
    It can be either an instant in time or 
    A period of time.
    """

    def __init__(self, start_time=None, end_time=None, stride=ONE_HOUR):
        """Initializes the data array
        """
        self.name = "OM_phenomenonTime"
        super(PhenomenonTime,self).__init__(start_time, end_time, stride)       

class ValidTime(Time):
    """Class representing the valid time.
    The valid time is the time of intended use.
    Must be a period of time.
    """

    def __init__(self, start_time=None, end_time=None, stride=ONE_HOUR, offset=0):
        """Initializes the data array.
        offset can be:
        a function that is applied to the data array, 
        a timedelta duration, 
        a datetime fixed date, or 
        a 0 representing an unlimited valid time
        """
        self.name = 'OM_validTime'
        super(ValidTime,self).__init__(start_time, end_time, stride)       
        self.metadata['standard_name'] = 'time'
        self.add_offset(offset)

    def add_offset(self, offset):
        """Offset can be:
        a function that is applied to the data array, 
        a timedelta duration, 
        a datetime fixed date, or 
        a 0 representing an unlimited valid time
        """
        o_type = type(offset)
        is_a_function = callable(offset)

        if is_a_function:
            for i,value in enumerate(self.data):
                self.data[i] = offset(value)

        elif o_type is timedelta:
            start_time = self.data.copy()
            end_time = self.data.copy()
            for i,value in enumerate(self.data):
                end_time[i] += offset.total_seconds()
            self.data = np.vstack((start_time,end_time))

        elif o_type is datetime:
            end_time = np.zeros(self.data.shape)
            end_time[:] = epoch_time(offset)
            start_time = self.data 
            self.data = self.data.vstack((start_time, end_time))
        # Assume data is valid indefinitely 
        elif o_type is int and offset == 0:
            #min_int = -sys.maxint - 1
            start_time = self.data.copy()
            end_time = np.zeros(self.data.shape)
            end_time[:] = FILL_VALUE
            self.data = np.vstack((start_time, end_time))

class ResultTime(Time):
    """Class representing the Result time.
    The result time is when the result (analysis, forcast)
    became available to data consumers.
    Must be an instant in time.
    """
    def __init__(self, start_time=None, end_time=None, stride=ONE_HOUR, result_time=None):
        """Initializes the data array
        """
        self.name = 'OM_resultTime'
        super(ResultTime,self).__init__(start_time, end_time, stride)       
        self.metadata['standard_name'] = 'time'
        self.append_result(result_time)
        
    def append_result(self, result_time):
        """Adds the Result Time.
        """

        ###
        # Below is what you would need if it was the time this variable was
        # created. Keeping in case we change our mind.
        ##
        #if result_time is None:
        #    #Return current time rounded to the next hour
        #    r = datetime.now()
        #    r = datetime(year=r.year, month=r.month,day=r.day, hour=r.hour+1)
        #    self.data[:] = epoch_time(r)
        o_type = type(result_time)
        if result_time is None:
            pass
        elif o_type is timedelta:
            for i,value in enumerate(self.data):
                self.data[i] = epoch_time(datetime.now() + result_time)

        elif o_type is datetime or o_type is str:
            self.data[:] = epoch_time(result_time)
                
        elif o_type is int:
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
        self.name = 'forecast_reference_time'
        super(ForecastReferenceTime,self).__init__(start_time, end_time, stride)       
        self.metadata['standard_name'] = self.name
        if reference_time is not None:
            self.append_reference_time(reference_time)
       
    def append_reference_time(self, result_time):
        self.data[:] = result_time

class LeadTime(Time): 
    """Class representing the lead time.
    The lead_time Length of time (a duration) from 
    forecast_reference_time to the
    Phenomenon time
    """
    #def __init__(self, start_time=None, end_time=None, stride=ONE_HOUR, lead=None):
    def __init__(self, **kwargs):
        """
        Initializes the data array
        """
        super(LeadTime,self).__init__(start_time, end_time, stride)       
        self.name = "LeadTime"
        stride = ONE_HOUR
        start_time = None
        end_time = None
        try:
            start_time = kwargs['start_time']
            end_time = kwargs['end_time']
            stride = kwargs['stride']
        except KeyError:
            pass
        if 'lead' in kwargs and kwargs['lead'] is timedelta:
            self.data[:] = lead.total_seconds()
            self.data[:] = lead
        super(LeadTime,self).__init__(start_time, end_time, stride)       
        self.metadata['standard_name'] = "forecast_period"
        self.metadata['units'] = 'seconds'
        if 'data' in kwargs:
            self.data = kwargs['data']

        #is_ref_time = type(forecast_ref_time) is ForecastReferenceTime
        #is_phenom_time = type(phenom_tim) is PhenomenonTime
        #if is_ref_time and is_phenom_time:
        #    self.data = phenom_time - forecast_ref_time

    def get_dimension_name(self):
        """Provides a way for accessing the name of the time dimension for leadtime."""
        return cfg.read_dimensions()['lead_time']
        

class BoundedTime(Time):
    """Class reproesenting the Bounded time. 
    The bounded time represents an instant in time 
    separated duration
    """
    def __init__(self, start_time=None, end_time=None, stride=ONE_HOUR, offset=None):
        """
        Initializes the data array
        """
        self.name = 'time_bounds'
        super(BoundedTime,self).__init__(start_time, end_time, stride)       
        self.metadata['standard_name'] = 'bounded_time'
        self.add_bounds(stride,offset)
    
    def add_bounds(self, stride, offset):
        """
        adds a bounds array to the object, where stride is 
        the number of time steps to skip, and offset is the
        starting point in the array
        """
        if type(offset) is list:
            for i in range(0, len(self.data)):
                if epoch_to_datetime(self.data[i]) not in offset:
                    self.data[i] = FILL_VALUE
            return
        elif type(offset) is int:
            self.duration = offset
            for i in range(0, len(self.data)):
                if i % offset != 0:
                    self.data[i] = FILL_VALUE
            return
        raise AssertionError("Offset type not recognized")

    def get_duration(self):
        try:
            return self.duration
        except:
            if len(self.data) >= 2:
                return self.data[1] - self.data[0]

    def add_common_metadata(self, nc_var):
        """Adds metadata that is common to Time variables.
        """
        setattr(nc_var, 'calendar', 'gregorian')
        setattr(nc_var, 'units', 'seconds')
        try:
            setattr(nc_var, 'interval', self.duration)
        except:
            pass

def alt_arr_equal(arr1, arr2, confidence='LOW'):
    """
    Determines if two arrays are equal. 
    Confidence can be 'LOW', 'MEDIUM', or 'HIGH'
    """
    len_arr1 = len(arr1)
    len_arr2 = len(arr2)
    if len_arr1 != len_arr2:
        return False
    if confidence == 'LOW':
        first_eq = arr1[0] == arr2[0]
        last_eq = arr1[-1] == arr2[-1]
        return first_eq and last_eq
    elif confidence == 'MEDIUM' :
        pass

    elif confidence == 'HIGH' :
        pass

