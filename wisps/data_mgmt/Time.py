import sys
import os
import numpy as np
import re
import pdb
from datetime import datetime
from datetime import timedelta
from nc_writable import nc_writable
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
import registry.util as cfg

##
# class Time()
# class PhenomenonTime(Time)
# class ValidTime(Time)
# class ResultTime(Time)
# class ForecastReferenceTime(Time)
# class LeadTime(Time)
# class BoundedTime(Time)
##

# Common amounts of time in seconds
ONE_MINUTE = 60
ONE_HOUR = ONE_MINUTE * 60
ONE_DAY = ONE_HOUR * 24
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
    start, end = sample_string.split("/")
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
        hour = int(time[8:10])
    except Exception:
        hour = 0
    try:
        minute = int(time[10:12])
    except Exception:
        minute = 0
    return datetime(year, month, day, hour, minute)


def epoch_to_datetime(seconds):
    """Converts epoch time to datetime"""
    return datetime.utcfromtimestamp(seconds)


def epoch_time(time):
    """Return hours array as seconds since the epoch,
    where time can be a datetime or str
    """
    if type(time) is not datetime and type(time) is not str and type(time) is not np.string_:
        raise TypeError("argument is not of type datetime or str")
    if type(time) is str or type(time) is np.string_:
        time = str_to_datetime(time)
    epoch = datetime.utcfromtimestamp(0)

    def unix_time(dt): return (dt - epoch).total_seconds()
    seconds_since_epoch = unix_time(time)
    # Remove the microsecond precision
    seconds_since_epoch = int(seconds_since_epoch)
    return seconds_since_epoch


def num_timesteps(start_time, end_time, stride=timedelta(hours=1)):
    """Calculates the number of timesteps between
    a start and end time with a certain duration.
    Assumes inclusive start and end times.
    """
    duration = end_time - start_time
    total_seconds = int(duration.total_seconds())
    timesteps = int(total_seconds / stride.total_seconds())
    timesteps += 1  # To keep end time inclusive
    return timesteps


def get_time_dim_name():
    """Provides a way for accessing the name of the time dimension."""
    return cfg.read_dimensions()['time']


def get_lead_dim_name():
    """Provides a way for accessing the name of the time dimension."""
    return cfg.read_dimensions()['lead_time']


def epoch_to_datetime(seconds):
    """Converts epoch time to datetime"""
    return datetime.utcfromtimestamp(seconds)


#def epoch_time(time):
#    """Return hours array as seconds since the epoch """
#    if type(time) is not datetime and type(time) is not str and not np.string_:
#        raise TypeError("argument is not of type datetime or str")
#    if type(time) is str or type(time) is np.string_:
#        time = str_to_datetime(time)
#    epoch = datetime.utcfromtimestamp(0)
#
#    def unix_time(dt): return (dt - epoch).total_seconds()
#    seconds_since_epoch = unix_time(time)
#    return seconds_since_epoch


class Time(nc_writable):
    """Baseclass representing time.
    """

    #def __init__(self, start_time=None, end_time=None, stride=ONE_HOUR):
    def __init__(self, **kwargs):
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

        if 'start_time' in kwargs:
            start_time = kwargs['start_time']
            end_time = kwargs['end_time']
            try:
                stride = kwargs['stride']
            except:
                stride = ONE_HOUR
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
        dim_tuple = self.get_dimensions() 
        self.create_missing_dimensions(nc_handle, dim_tuple)
        dim_tuple = self.check_dimensions(nc_handle, dim_tuple)

        name, exists = self.get_name(nc_handle)
        if not exists:
            nc_time = nc_handle.createVariable(
                name,
                int,
                dimensions=dim_tuple,
                fill_value=-FILL_VALUE)
            nc_time[:] = self.data
            self.add_common_metadata(nc_time)
            # Add special Metadata
            for meta_name, value in self.metadata.iteritems():
                setattr(nc_time, meta_name, value)
        return name

    def get_dimensions(self):
        """Return a tuple of dimension names. 
        Will account for data with different shapes.
        """
        dim_tuple = (get_time_dim_name(),)
        assert len(dim_tuple) == len(self.data.shape)
        return dim_tuple

    def create_missing_dimensions(self, nc_handle, dimensions):
        """given iterable list of dimensions, 
        creates dimensions.
        """
        for i,dim in enumerate(dimensions):
            if dim not in nc_handle.dimensions:
                nc_handle.createDimension(dim, self.data.shape[i])


    def get_name(self, nc_handle):
        """Looks for a match in Time variables.
        Returns a tuple containing the [0] - name of the variable
        and [1] - a boolean indicating if it already existed.
        """
        all_vars = nc_handle.variables
        varkeys = all_vars.keys()

        def match(var): return re.match(r'^' + self.name + '\d*$', var, re.I)
        time_vars = filter(match, varkeys)
        for name in reversed(time_vars):
            var = all_vars[name]
            # Check for a data match
            if np.array_equal(var[:], self.data):
                return (name, True)
        if len(time_vars) == 0:
            name = self.name
        else:
            name = self.name + str(len(time_vars))
        return (name, False)

    def get_stride(self, as_timedelta=False):
        """Returns the number of seconds between two time steps.
        This function may provide misleading information if timesteps
        have an irregular step duration.
        """
        size = len(self.data)
        if size <= 1:
            raise IndexError("Time data has 1 or 0 elements")
        if len(self.data.shape) == 2:
            start = self.data[0][0]
            end = self.data[1][0]
        else:
            sample_data = self.data.flatten()
            start = sample_data[0]
            end = sample_data[1]
        stride = end - start
        if as_timedelta:
            return timedelta(seconds=stride)
        return stride

        size = len(self.data)
        if size <= 1:
            raise IndexError("Time.data.")
        start = self.data[9]

    def _search_equal_size(self, nc_dimensions, dim, size):
        """Searches for a dimension that equals the size of the dim.
        """
        for nc_dim in nc_dimensions.keys():
            if dim in nc_dim and len(nc_dimensions[nc_dim]) == size:
                return nc_dim
            
    def is_duration(self):
        """Returns if the current object is a type of duration
        """
        return False

    def check_dimensions(self, nc_handle, dim_tuple):
        """Check data dimension shape is equal to the nc handle dimension.
        """
        dim_list = list(dim_tuple)
        shape = self.data.shape
        nc_dims = nc_handle.dimensions
        for i, (dim, size) in enumerate(zip(dim_list,shape)):
            nc_len = nc_dims[dim] 
            count = 0
            if size != nc_len:
                name = self._search_equal_size(nc_dims, dim, size)
                if name is not None: 
                    dim_list[i] = name
                else: # It hasn't been created yet, so create it.
                    count = 0
                    stride = self.get_stride()
                    hours = int(stride/3600)
                    name = dim + '_' + str(hours) + 'hr'
                    alt_name = name
                    while alt_name in nc_dims:
                        count += 1
                        alt_name = name + '_' + str(count)
                    nc_handle.createDimension(alt_name, size)
                    dim_list[i] = alt_name

        return tuple(dim_list)

        shape = self.data.shape
        time_dim = get_time_dim_name()
        nc_dim_size = len(nc_handle.dimensions[time_dim])
        size = shape[0]
        if size != nc_dim_size:
            # Find if one has already been created
            try:
                count = 0
                while True:
                    offset = "1"
                    if len(self.data) > 2:
                        offset = str(
                            (self.data[1] - self.data[0]) / 3600) + 'hr'
                    alt_dim_name = time_dim + "_" + offset
                    if count > 0:
                        alt_dim_name = time_dim + "_" + \
                            offset + ' ' + str(count)
                    count += 1
                    nc_dim_size = len(nc_handle.dimensions[alt_dim_name])
                    if size == nc_dim_size:
                        return alt_dim_name
            except KeyError:
                nc_handle.createDimension(alt_dim_name, size)
                return alt_dim_name

    def add_common_metadata(self, nc_var):
        """Adds metadata that is common to Time variables.
        """
        setattr(nc_var, 'calendar', 'gregorian')
        setattr(nc_var, 'units', 'seconds since 1970-01-01 00:00:00.0')


    def get_bounded_dimension_name(self):
        """Provides a way for accessing the name of the start and end
        dimension.
        """
        return 'begin_end_size'

    def get_start_time(self):
        return epoch_to_datetime(int(self.data.flatten()[0]))

    def get_end_time(self):
        return epoch_to_datetime(int(self.data.flatten()[-1]))

    def __add__(self, other):
        """ overloading + opporator """
        if type(self) is type(other):
            self.data = np.append(self.data, other.data)
            return self

    def __str__(self):
        ret_str = "** " + self.name + " **" + "\n"
        ret_str += "Shape:  "
        ret_str += str(self.data.shape) + "\n"
        if len(self.data) > 0 and len(self.data.shape) == 1:
            ret_str += "start_time: "
            ret_str += str(epoch_to_datetime(self.data[0])) + "\n"
            ret_str += "end_time:   "
            ret_str += str(epoch_to_datetime(self.data[-1])) + "\n"
            ret_str += "Timesteps:  "
            ret_str += str(len(self.data)) + "\n"
            ret_str += "Data: \n"
            ret_str += "[" + str(epoch_to_datetime(self.data[0])) + ", "
            ret_str += str(epoch_to_datetime(self.data[1])) + ",\n"
            ret_str += "  ....\n"
            ret_str += str(epoch_to_datetime(self.data[-2])) + ", "
            ret_str += str(epoch_to_datetime(self.data[-1])) + "]"
        elif len(self.data) > 0 and len(self.data.shape) == 2:
            ret_str += "Data: \n"
            ret_str += "[" + str(epoch_to_datetime(self.data[0][0])) + ", "
            ret_str += str(epoch_to_datetime(self.data[0][1])) + ",\n"
            ret_str += "  ....\n"
            ret_str += str(epoch_to_datetime(self.data[-1][-2])) + ", "
            ret_str += str(epoch_to_datetime(self.data[-1][-1])) + "]"
        ret_str += "\n"
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

    #def __init__(self, start_time=None, end_time=None, stride=ONE_HOUR):
    def __init__(self, **kwargs):
        """Initializes the data array
        """
        self.name = "OM_phenomenonTime"
        if 'start_time' in kwargs:
            start_time = kwargs['start_time']
            end_time = kwargs['end_time']
            try:
                stride = kwargs['stride']
            except:
                stride = ONE_HOUR

            super(PhenomenonTime, self).__init__(start_time=start_time,
                                                 end_time=end_time,
                                                 stride=stride)
        elif 'data' in kwargs:
            super(PhenomenonTime, self).__init__()
            self.data = kwargs['data']

    def get_dimensions(self):
        """Return a tuple of dimension names. 
        Will account for data with different shapes.
        """
        num_dims = len(self.data.shape)
        if num_dims == 1:
            dim_tuple = (get_time_dim_name(),)
        elif num_dims == 2:
            dim_tuple = (get_lead_dim_name(), get_time_dim_name())
        else:
            raise AssertionError("more than 2 dimensions describing time")

        assert len(dim_tuple) == len(self.data.shape)
        return dim_tuple


class ValidTime(Time):
    """Class representing the valid time.
    The valid time is the time of intended use.
    Must be a period of time.
    """

    def __init__(self, **kwargs): #start_time=None, end_time=None, stride=ONE_HOUR, offset=0):
        """Initializes the data array.
        offset can be:
        a function that is applied to the data array,
        a timedelta duration,
        a datetime fixed date, or
        a 0 representing an unlimited valid time
        """
        self.name = 'OM_validTime'
        if 'start_time' in kwargs:
            start_time = kwargs['start_time']
            end_time = kwargs['end_time']
            try:
                stride = kwargs['stride']
            except:
                stride = ONE_HOUR
            super(ValidTime, self).__init__(start_time=start_time,
                                          end_time=end_time,
                                          stride=stride)
            try:
                offset = kwargs['offset']
            except:
                offset = 0
            self.add_offset(offset)
        elif 'data' in kwargs:
            super(ValidTime, self).__init__()
            self.data = kwargs['data']
            offset = 0

        self.metadata['standard_name'] = 'time'


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
            for i, value in enumerate(self.data):
                self.data[i] = offset(value)

        elif o_type is timedelta:
            start_time = self.data.copy()
            end_time = self.data.copy()
            for i, value in enumerate(self.data):
                end_time[i] += offset.total_seconds()
            self.data = np.vstack((start_time, end_time))

        elif o_type is datetime:
            end_time = np.zeros(self.data.shape)
            end_time[:] = epoch_time(offset)
            start_time = self.data
            self.data = np.vstack((start_time, end_time))
        # Assume data is valid indefinitely
        elif o_type is int and offset == 0:
            # min_int = -sys.maxint - 1
            start_time = self.data.copy()
            end_time = np.zeros(self.data.shape)
            end_time[:] = FILL_VALUE
            self.data = np.vstack((start_time, end_time))

    def get_dimensions(self):
        """Return a tuple of dimension names. 
        Will account for data with different shapes.
        """
        if len(self.data.shape) == 2:
            dim_tuple = (self.get_bounded_dimension_name(),
                         get_time_dim_name())
        elif len(self.data.shape) == 3:
            dim_tuple = (get_lead_dim_name(),
                         get_time_dim_name(),
                         self.get_bounded_dimension_name())
        assert len(dim_tuple) == len(self.data.shape)
        return dim_tuple


class ResultTime(Time):
    """Class representing the Result time.
    The result time is when the result (analysis, forcast)
    became available to data consumers.
    Must be an instant in time.
    """

    def __init__(self, **kwargs): # start_time=None, end_time=None, stride=ONE_HOUR, result_time=None):
        """Initializes the data array
        """
        self.name = 'OM_resultTime'
        if 'start_time' in kwargs:
            start_time = kwargs['start_time']
            end_time = kwargs['end_time']
            try:
                stride = kwargs['stride']
            except:
                stride = ONE_HOUR
            super(ResultTime, self).__init__(start_time=start_time,
                                        end_time=end_time,
                                        stride=stride)
        if 'data' in kwargs:
            super(ResultTime, self).__init__()
            self.data = kwargs['data']
        self.metadata['standard_name'] = 'time'
        if 'result_time' in kwargs:
            result_time = kwargs['result_time']
            self.append_result(result_time)

    def append_result(self, result_time):
        """Adds the Result Time.
        """

        ###
        # Below is what you would need if it was the time this variable was
        # created. Keeping in case we change our mind.
        ##
        # if result_time is None:
        #    #Return current time rounded to the next hour
        #    r = datetime.now()
        #    r = datetime(year=r.year, month=r.month,day=r.day, hour=r.hour+1)
        #    self.data[:] = epoch_time(r)
        o_type = type(result_time)
        if result_time is None:
            pass
        elif o_type is timedelta:
            for i, value in enumerate(self.data):
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

    def __init__(self, **kwargs): #start_time=None, end_time=None, stride=ONE_HOUR, reference_time=None):
        """
        Initializes the data array
        """
        self.name = 'forecast_reference_time'
        if 'start_time' in kwargs:
            start_time = kwargs['start_time']
            end_time = kwargs['end_time']
            try:
                stride = kwargs['stride']
            except:
                stride = ONE_HOUR
            super(ForecastReferenceTime, self).__init__(start_time=start_time,
                                                    end_time=end_time,
                                                    stride=stride)
        elif 'data' in kwargs:
            super(ForecastReferenceTime, self).__init__()
            self.data = kwargs['data']
        self.metadata['standard_name'] = self.name
        if 'reference_time' in kwargs:
            self.append_reference_time(kwargs['reference_time'])

    def append_reference_time(self, ref_time):
        self.data[:] = ref_time


class LeadTime(Time):
    """Class representing the lead time.
    The lead_time Length of time (a duration) from
    forecast_reference_time to the
    Phenomenon time
    """
    # def __init__(self, start_time=None, end_time=None, stride=ONE_HOUR,
    # lead=None):

    def __init__(self, **kwargs):
        """
        Initializes the data array
        """
        self.name = "LeadTime"
        stride = ONE_HOUR
        start_time = None
        end_time = None
        if 'start_time' in kwargs:
            start_time = kwargs['start_time']
            end_time = kwargs['end_time']
            try:
                stride = kwargs['stride']
            except:
                stride = ONE_HOUR
            super(LeadTime, self).__init__(start_time=start_time,
                                        end_time=end_time,
                                        stride=stride)
            if 'lead' in kwargs and kwargs['lead'] is timedelta:
                lead = kwargs['lead']
                self.data[:] = lead.total_seconds()
        elif 'data' in kwargs:
            super(LeadTime, self).__init__()
            self.data = kwargs['data']

        self.metadata['standard_name'] = "forecast_period"

        # is_ref_time = type(forecast_ref_time) is ForecastReferenceTime
        # is_phenom_time = type(phenom_tim) is PhenomenonTime
        # if is_ref_time and is_phenom_time:
        #    self.data = phenom_time - forecast_ref_time
    def get_dimensions(self):
        """Return a tuple of dimension names. 
        Will account for data with different shapes.
        """
        dim_tuple = (get_lead_dim_name(),)
        assert len(dim_tuple) == len(self.data.shape)
        return dim_tuple

    def __str__(self):
        ret_str = "** " + self.name + " **" + "\n"
        ret_str += "Number of lead times: \n"
        ret_str += str(len(self.data.shape)) + "\n"
        ret_str += "Data:\n"
        if len(self.data) > 6:
            for i in range(3):
                ret_str += str(self.data[i]/3600)
                ret_str += "hr,\n"
            ret_str += "   ...\n"
            for i in range(-3,0):
                ret_str += str(self.data[i]/3600)
                ret_str += "hr,\n"
        return ret_str


class BoundedTime(Time):
    """Class reproesenting the Bounded time.
    The bounded time represents an instant in time
    separated duration
    """

    def __init__(self, **kwargs):#start_time=None, end_time=None, stride=ONE_HOUR, offset=None):
        """
        Initializes the data array
        """
        self.name = 'time_bounds'
        if 'start_time' in kwargs:
            start_time = kwargs['start_time']
            end_time = kwargs['end_time']
            try:
                stride = kwargs['stride']
            except:
                stride = ONE_HOUR
            super(BoundedTime, self).__init__(start_time=start_time,
                                        end_time=end_time,
                                        stride=stride)
        if 'data' in kwargs:
            super(BoundedTime, self).__init__()
            self.data = kwargs['data']

        offset=None
        if 'offset' in kwargs:
            offset = kwargs['offset']
            self.add_bounds(stride, offset)
        self.metadata['standard_name'] = 'bounded_time'

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


def fast_arr_equal(arr1, arr2):
    """
    Determines if two arrays are equal.
    Confidence is low that they are indeed equal
    """
    len_arr1 = len(arr1)
    len_arr2 = len(arr2)
    if len_arr1 != len_arr2:
        return False
    first_eq = arr1[0] == arr2[0]
    last_eq = arr1[-1] == arr2[-1]
    return first_eq and last_eq
