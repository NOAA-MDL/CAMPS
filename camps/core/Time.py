import sys
import os
import numpy as np
import re
import logging
import pdb
from time import tzname
from datetime import datetime
from datetime import timedelta
from .nc_writable import nc_writable
from ..registry import util as cfg


"""Module: Time.py

Methods
    parse_ISO_standard_time
    parse_development_sample
    parse_forecast_reference_time
    datetime_to_str
    str_to_datetime
    epoch_to_datetime
    epoch_time
    num_timesteps
    get_time_dim_name
    get_lead_dim_name
    fast_arr_equal

Classes
    Time(nc_writable)
        Methods
            __init__
            init_time_data
            get_fill_value
            write_to_nc
            get_dimensions
            create_missing_dimensions
            get_name
            get_stride
            _search_equal_size
            is_duration
            check_dimensions
            add_common_metadata
            get_bounded_dimension_name
            get_start_time
            get_end_time
            __add__
            __str__
            __eq__

    PhenomenonTimePeriod(Time)
        Methods
            __init__
            get_duration
            write_to_nc
            get_dimensions
            get_index
            write_begin_end_var
            get_name
            get_stride

    PhenomenonTime(Time)
        Methods
            __init__
            get_dimensions
            get_index

    ValidTime(Time)
        Methods
            __init__
            add_offset
            get_dimensions
            get_stride

    ResultTime(Time)
        Methods
            __init__
            append_result

    ForecastReferenceTime(Time)
        Methods
            __init__
            get_index
            append_reference_time

    LeadTime(Time)
        Methods
            __init__
            get_dimensions
            get_index
            add_common_metadata
            __add__
            __str__
"""


#Common amounts of time in seconds
ONE_MINUTE = 60
ONE_HOUR = ONE_MINUTE * 60
ONE_DAY = ONE_HOUR * 24
FILL_VALUE = -9999


#Common time interpretation functions

def parse_ISO_standard_time(time):
    """Convert to epoch time a string that is the
    ISO standard representation of time, YYYY-MM-DD.
    """

    #NOTE: Incomplete
    pass


def parse_development_sample(sample_str):
    """Given a string with an ISO interval representation,
    such as 2014-04-01/2014-09-30, returns tuple (start date, end date)
    in datetime format.
    """

    start, end = sample_string.split("/")
    dt_start = datetime(year=start[:4], month=start[5:7], day=start[8:])
    dt_end = datetime(year=end[:4], month=end[5:7], day=end[8:])

    return (dt_start, dt_end)


def parse_forecast_reference_time(forecast_str):
    """Given a string of type YYYY-MM-DDTFF, returns the FF component,
    which represents the forecast reference time as a tuple, where
    index 0 = number of hours and
    index 1 = number of seconds
    """

    hours = forecast_str[11:]
    hours = int(hours)
    seconds = hours * ONE_HOUR

    return (hours, seconds)


def datetime_to_str(time):
    """Convert a datetime object time into the format YYYYMMDDHH."""

    return str(time.year).zfill(4) + \
        str(time.month).zfill(2) + \
        str(time.day).zfill(2) + \
        str(time.hour).zfill(2)


def str_to_datetime(time):
    """Convert time in form YYYYMMDDHH to datetime format."""

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
    """Return time as seconds since the epoch,
    where time can be a datetime or str.
    """
    #time must be a datetime object, str object, or an array of fixed-width byte strings.
    if type(time) is not datetime and type(time) is not str and type(time) is not np.str_:
        raise TypeError("argument is not of type datetime or str")

    #Convert time of type string to that of type datetime.
    if type(time) is str or type(time) is np.str_:
        time = str_to_datetime(time)

    #Get start of epoch in datetime format
    if "UTC" in tzname[0]:
        epoch = datetime.utcfromtimestamp(0)
    else:
        epoch = datetime.fromtimestamp(0)

    #Get seconds since epoch start in datetime format
    seconds_since_epoch = (time-epoch).total_seconds()

    #Return integer version
    return int(seconds_since_epoch)


def num_timesteps(start_time, end_time, stride=timedelta(hours=1)):
    """Calculates the number of timesteps between a start and
    end time with a stride of type timedelta.  Default value of stride is 1 hour.
    Assumes inclusive start and end times.
    """

    duration = end_time - start_time
    total_seconds = int(duration.total_seconds())
    timesteps = int(total_seconds / stride.total_seconds())
    timesteps += 1  #keep end time inclusive

    return timesteps


def get_time_dim_name():
    """Returns the name of the time dimension."""

    return cfg.read_dimensions()['time']


def get_lead_dim_name():
    """Returns the name of the lead time dimension."""

    return cfg.read_dimensions()['lead_time']



class Time(nc_writable):
    """Baseclass representing time.
    Inherits from class nc_writable.
    """

    def __init__(self, **kwargs):
        """Initializes the valid_time, result_time, phenomenon_time,
        and lead time arrays.
        """

        self.data = np.array([], dtype=int)
        self.metadata = {}
        try:
            self.metadata['PROV__specializationOf'] = "( " + self.name + " )"
        except:
            self.name = "time"
            self.metadata['PROV__specializationOf'] = "( " + self.name + " )"

        if 'start_time' in kwargs and 'end_time' in kwargs:
            start_time = kwargs['start_time']
            end_time = kwargs['end_time']
            try:
                stride = kwargs['stride']
            except:
                stride = ONE_HOUR
            self.init_time_data(start_time, end_time, stride)

    def init_time_data(self, start_date, end_date, stride):
        """Fills the arrays with appropriate data in datetime format.
        start and end dates can be of type datetime, str (YYYYMMDD),
        or int (epoch time in seconds).  end_time is non-inclusive.
        """

        #Convert start date to datetime format.
        if type(start_date) == str:
            start_date = str_to_datetime(start_date)
        elif type(start_date) == int:
            start_date = epoch_to_datetime(start_date)

        #Convert end date to datetime format.
        if type(end_date) == str:
            end_date = str_to_datetime(end_date)
        elif type(end_date) == int:
            end_date = epoch_to_datetime(end_date)

        #Convert stride to timedelta format
        if type(stride) == str:
            stride = int(str)
        elif type(stride) is not timedelta:
            stride = timedelta(seconds=stride)

        #Fill time data array with values resulting
        #from stepping from start time to end time
        #with a specified stride.
        temp = []
        cur_date = start_date
        while 1:
            temp.append(epoch_time(cur_date))
            cur_date += stride
            if cur_date > end_date: break
        self.data = np.asarray(temp,dtype=np.int64)


    def get_fill_value(self):
        """Returns the fill value popped out of the variable's metadata, or
        its default value if it is not in metadata.
        """

        #Variable can not be written into a netCDF file if it
        #has _FillValue as an attribute.  Thus it is popped out
        #of metadata.  The key 'fill_value' has priority over
        #the key '_FillValue'.
        if "fill_value" in self.metadata:
            return self.metadata.pop("fill_value")

        elif "_FillValue" in self.metadata:
            return self.metadata.pop('_FillValue')

        #Return default value.
        return FILL_VALUE


    def write_to_nc(self, nc_handle):
        """Create a Time variable for a netCDF Dataset."""

        #Ensure Time variable names and dimensions match.
        dim_tuple = self.get_dimensions() #Collect Time variable dimensions into a tuple
        self.create_missing_dimensions(nc_handle, dim_tuple) #Ensure Time variable dimension names are in netCDF Dataset
        dim_tuple = self.check_dimensions(nc_handle, dim_tuple) #Ensure Time variable dimensions are matched by
                                                                #name and SIZE with dimensions in netCDF Dataset
        #Get fill value from Time data array
        fill_value = self.get_fill_value()

        #Create variable in netCDF Dataset if it currently does not exist there.
        name, exists = self.get_name(nc_handle)
        if not exists:
            nc_time = nc_handle.createVariable(
                name,
                int,
                dimensions=dim_tuple,
                fill_value=-FILL_VALUE) #NOTE: doesn't use value obtained above from get_fill_value()
            #Add Time variable's data
            nc_time[:] = self.data
            #Add attributes
            self.add_common_metadata(nc_time)
            for meta_name, value in self.metadata.items():
                setattr(nc_time, meta_name, value)

        #Return the name of the Time variable.
        return name


    def get_dimensions(self):
        """Return a tuple of time dimension names."""

        dim_tuple = (get_time_dim_name(),)

        #Number of dimensions must match
        assert len(dim_tuple) == len(self.data.shape)

        return dim_tuple


    def create_missing_dimensions(self, nc_handle, dimensions):
        """Creates into the netCDF Dataset the elements in 'dimensions'
        that are missing in Dataset.
        """

        for i,dim in enumerate(dimensions):
            if dim not in nc_handle.dimensions:
                nc_handle.createDimension(dim, self.data.shape[i])


    def get_name(self, nc_handle):
        """Returns a tuple containing the
        [0] - name of the netCDF Dataset time variable and
        [1] - a boolean indicating if it already exists as a netCDF Dataset variable.
        Beforehand, if there is no match of
        1) the variable name and
        2) variable data array size
        in netCDF Dataset, then it adjusts the digital suffix of the name
        for the netCDF Dataset time variable.
        """

        all_vars = nc_handle.variables
        varkeys = list(all_vars.keys())

        #Matching pattern consists of Time variable name plus a digital suffix.
        #Case of letters are immaterial.
        def match(var): return re.match(r'^' + self.name + '\d*$', var, re.I)
        time_vars = list(filter(match, varkeys)) #gleans the matching names from netCDF Dataset
        for name in reversed(time_vars):
            var = all_vars[name]
            #Return name and True with first match in data array.
            if np.array_equal(var[:], self.data):
                return (name, True)

        #No match.  Make name.
        if len(time_vars) == 0:
            name = self.name
        else:
            name = self.name + str(len(time_vars))
        return (name, False)


    def get_stride(self, as_timedelta=False):
        """Returns as an int object the number of seconds between the
        first two time steps in a series of time values, unless
        'as_timedelta' is True.  Then it is returned as a timedelta object.
        Beware of assuming this 'stride' holds throughout the series.
        """

        #Determining stride requires data with more than one element
        size = len(self.data)
        if size <= 1:
            raise IndexError("Time data has 1 or 0 elements")

        #Determine the stride.
        if len(self.data.shape) == 2:
            #start and end of first stride in a series of durations.
            start = self.data[0][0] #start of first duration
            end = self.data[1][0] #start of second duration
        else:
            #start and end of first stride in a series of singular times
            sample_data = self.data.flatten()
            start = sample_data[0]
            end = sample_data[1]
        stride = end - start

        #Return stride as timedelta object as requested in setting as_timedelta to True
        if as_timedelta:
            return timedelta(seconds=stride)

        return stride


    def _search_equal_size(self, nc_dimensions, dim, size):
        """Returns a netCDF Dataset dimension with a size equal to
        'size' of the variable dimension 'dim'.  Otherwise, returns None.
        """

        for nc_dim in list(nc_dimensions.keys()):
            if dim in nc_dim and len(nc_dimensions[nc_dim]) == size:
                return nc_dim

        return None


    def is_duration(self):
        """Returns True if the variable has a duration dimension."""

        dim_names = self.get_dimensions()
        duration_dim = get_bounded_dimension_name()
        if duration_dim in dim_names:
            return True

        return False


    def check_dimensions(self, nc_handle, dim_tuple):
        """Ensures that for each variable dimension there is a netCDF Dataset counterpart with
        the same name and the same size.  This may require renaming the variable dimension name
        or creating a new netCDF Dataset dimension.  Returns the potentially modified variable
        dimension name list as a tuple.
        """

        dim_list = list(dim_tuple)
        shape = self.data.shape #'dim_list' and 'shape' have same dimensions per get_dimensions
        nc_dims = nc_handle.dimensions
        #Loop by variable dimension
        for i, (dim, size) in enumerate(zip(dim_list,shape)): #name 'dim' and size 'size'
            nc_len = nc_dims[dim] #no KeyError per create_missing_dimensions
            #If sizes equal, got valid counterpart.  Otherwise, ...
#            count = 0
            if size != nc_len:
                #Search existing netCDF Dataset dimensions for one with equal size.  It will have differing name 'name'.
                name = self._search_equal_size(nc_dims, dim, size)
                if name is not None: #found
                    dim_list[i] = name #set variable dimension name to 'name'
                else: #not found
                    #Create a netCDF Dataset dimension and rename the variable dimension
                    count = 0
                    #stride = self.get_stride() #stride between time entries will be in dimension name
                    #hours = int(stride/3600)
                    #name = dim + '_' + str(hours) + 'hr'
                    name = dim
                    #Ensure that name of new dimension is unique via a digital suffix
                    alt_name = name
                    while alt_name in nc_dims:
                        count += 1
                        #alt_name = name + '_' + str(count)
                        alt_name = name + str(count)
                    nc_handle.createDimension(alt_name, size) #create the new netCDF Dataset dimension
                    dim_list[i] = alt_name #rename variable dimension name

        return tuple(dim_list)


    def add_common_metadata(self, nc_var):
        """Adds metadata that is common to Time variables."""

        setattr(nc_var, 'calendar', 'gregorian')
        setattr(nc_var, 'units', 'seconds since 1970-01-01 00:00:00.0')
        setattr(nc_var, 'standard_name', 'time')


    def get_bounded_dimension_name(self):
        """Returns the name of the bounded Time dimension."""

        return 'begin_end_size'


    def get_start_time(self):
        """Return as a datetime object the first element of a flattened Time data array."""

        return epoch_to_datetime(int(self.data.flatten()[0]))


    def get_end_time(self):
        """Return as a datetime object the last element of a flattened Time data array"""

        return epoch_to_datetime(int(self.data.flatten()[-1]))


    def __add__(self, other):
        """Overloading '+' operator for the Time class.  Concatenates the data arrays
           along the axis of the default time coordinate.
        """

        dim_tuple = self.get_dimensions()
        assert(dim_tuple == other.get_dimensions()),"Data of objects must have same dimensional axes."

        dim_name = get_time_dim_name() #get the default time dimension
        try:
            i = dim_tuple.index(dim_name) #id index
            self.data = np.concatenate((self.data, other.data), axis=i) #concatenate
        except ValueError:
            logging.info('Missing dimension {} along which to concatenate data.'.format(dim_name))
            #NOTE: raise an error, since concatentation failed?

        return self


    def __eq__(self, other):
        """Overload the '=' operator.  Return True if Time data arrays are equal."""

        #Time objects must be of same type
        if type(self) != type(other):
            return False

        return np.array_equal(self.data,other.data)


    def __str__(self):
        """Formatted response to typing the Time object name."""

        ret_str = "** " + self.name + " **" + "\n"
        ret_str += "Shape:  "
        ret_str += str(self.data.shape) + "\n"
        if self.data.size == 1:
            ret_str += "One timestep: "
            ret_str += self.data.__repr__()
        elif len(self.data) > 0 and len(self.data.shape) == 1:
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
            ret_str += str(epoch_to_datetime(self.data[-1])) + "]"
        elif len(self.data) > 0 and len(self.data.shape) == 2:
            ret_str += "Data: \n"
            ret_str += "[" + str(epoch_to_datetime(self.data[0][0])) + ", "
            ret_str += "  ....\n"
            ret_str += str(epoch_to_datetime(self.data[-1][-1])) + "]"
        ret_str += "\n"

        return ret_str


    __repr__ = __str__



class PhenomenonTimePeriod(Time):
    """Class representing the Phenomenon Time Period
    Phenomenon time is colloquially, when the weather happens.
    It can be either an instant in time or
    A period of time.
    """

    def __init__(self, **kwargs):
        """Initializes the data array
        """
        self.name = "OM__phenomenonTimePeriod"

        #Set the object's data, either by specifying the start and end times
        #along with the variable's period OR ... (see elif statement below)
        if 'start_time' in kwargs and 'end_time' in kwargs:
            start_time = kwargs['start_time']
            end_time = kwargs['end_time']
            try:
                stride = kwargs['stride']
            except:
                stride = ONE_HOUR

            super(PhenomenonTimePeriod, self).__init__(start_time=start_time,
                                                 end_time=end_time,
                                                 stride=stride)
            num_dimensions = len(self.data.shape)
            if 'period' in kwargs and num_dimensions == 1:
                period = int(kwargs['period'])
                # offset is in number of cells
                # So, if your period starts on the first time period
                # then offset would be 0.
                if 'offset' in kwargs:
                    offset = kwargs['offset']
                else:
                    offset = 0
                data_len = len(self.data)

                # Create an empty 2-D array of length (data_len,2)
                new_time = np.full((data_len,2), FILL_VALUE, int)

                # Loop through your array. Initialize i is needed here incase the for
                # loop does not trigger because of a singular date (i.e. no range).
                i = 0
                for i in range(offset,(data_len-period)+1,period):
                    new_time[i][0] = self.data[i]-(period*ONE_HOUR) # Beginning of time period
                    new_time[i][1] = self.data[i]                   # Ending of time period
                self.diff = new_time[i][1] - new_time[i][0] #diff is period in seconds, and
                self.duration = int(self.diff/3600)              #duration is periond in hours.


                self.data = new_time

        #OR by feeding in the period data itself.
        elif 'data' in kwargs:
            super(PhenomenonTimePeriod, self).__init__()

            data = np.asarray(kwargs['data']) #Convert data type to numpy.ndarray

            #Number of elements should be even.
            size = data.size
            assert(size > 1 and size % 2 == 0)

            #Note shape and number of dimensions
            shape = data.shape
            ndims = len(shape)
            if ndims > 1: #if number of dimensions greater than one,
                assert(shape[-1] == 2) #then size of last dimension should be two.

            #There should be at least one valid period entry.
            data = np.reshape(data, (-1, 2))
            i_valid = np.where((data[:,0] != FILL_VALUE) * (data[:,1] != FILL_VALUE))
            n_valid = len(i_valid[0])
            assert(n_valid > 0)

            #Valid entries should correspond to the same period value.
            data_valid = data[i_valid[0],:]
            periods = np.subtract(data_valid[:,1], data_valid[:,0])
            period = periods[0]
            np.testing.assert_equal( periods, np.full(len(periods), period) )

            #Recast data into its original shape if the number of dimensions is greater than two.
            #Note that data for ndims=1 is left as two-dimensional.
            if ndims > 2:
                data = np.reshape(data, shape)

            #Insert the data and the period into the PhenomenonTimePeriod object.
            self.data = data

            #diff is the predictor period in seconds and duration the period in hours.
            self.diff = period # Set duration of period (s)
            self.duration = int(self.diff/3600)

        self.metadata.update({ 'standard_name' : 'time' })
        self.metadata.update({ 'PROV__specializationOf' : '( StatPP__concepts/TimeBoundsSyntax/BeginEnd OM__phenomenonTimePeriod )' })


    def get_duration(self):
        """Returns True if duration is non-zero."""

        return self.duration


    def write_to_nc(self, nc_handle):
        """Writes to netCDF Dataset the variable of type PhenomenonTimePeriod."""

        name = super(PhenomenonTimePeriod, self).write_to_nc(nc_handle)

        return name


    def get_dimensions(self):
        """Returns a tuple of dimension names of the phenomenon time period data."""

        num_dims = len(self.data.shape)
        if num_dims == 2:
            dim_tuple = (get_time_dim_name(),self.get_bounded_dimension_name())
        elif num_dims == 3:
            dim_tuple = (get_lead_dim_name(), get_time_dim_name(), self.get_bounded_dimension_name())
        else:
            raise AssertionError("more than 3 dimensions describing time")

        #NOTE: Unnecessary assertion.  Above code guarantees the truth of this assertion.
        #Check that the number of dimension names agrees with the number of dimensions in the data.
        #assert len(dim_tuple) == len(self.data.shape)

        return dim_tuple


    def get_index(self, num_seconds):
        """Returns as a tuple the location in the PhenomenonTimePeriod object data
        of the first period with an end time equal to num_seconds.
        """

        num_dims = len(self.data.shape)
        if num_dims == 2:
            indices = np.where(self.data[:,1] == num_seconds)
            if len(indices[0]):
                if len(indices[0]) > 1:
                    print(("More than one period found in PhenomenonTimePeriod object with end time %d.", num_seconds))
                indices = int(indices[0][0]),
            else:
                print(("No period found in PhenomenonTimePeriod object with end_time %d found.", num_seconds))
        elif num_dims == 3:
            indices = np.where(self.data[:,:,1] == num_seconds)
            if len(indices[0]):
                if len(indices[0]) > 1:
                    print(("More than one period found in PhenomenonTimePeriod object with end time %d.", num_seconds))
                indices = int(indices[0][0]), int(indices[1][0])
            else:
                print(("No period found in PhenomenonTimePeriod object with end_time %d found.", num_seconds))
        else:
            raise AssertionError("The number of dimensions of the data of phenomenon time period must be 2 or 3.")

        return indices


    def write_begin_end_var(self, nc_handle):
        """Ensures that beg_end_bounds dimension is in the netCDF Dataset object."""

        bounds_dim_name = self.get_bounded_dimension_name()
        if(bounds_dim_name not in nc_handle.variables):
            bounds_var = nc_handle.createVariable(bounds_dim_name, int, dimensions=())
            setattr(bounds_var, bounds_dim_name, 'TM__Period:Beginning TM__Period:Ending')
            setattr(bounds_var, 'long_name', 'time bound description')


    def get_name(self, nc_handle):
        """Looks for a match of the PhenomenonTimePeriod variable to any netCDF Dataset variables.
        Returns a tuple containing the [0] - name of the variable
        and [1] - a boolean indicating if it already existed.
        """

        all_vars = nc_handle.variables #dictionary of netCDF Dataset variable objects
        varkeys = list(all_vars.keys()) #list of netCDF Dataset variable names

        #Match pattern consists of variable name, duration, and a digital suffix.
        period_name = self.name + str(int(self.diff/3600)) + 'hr'
        def match(var): return re.match(r'^' + period_name + '\d*$', var, re.I)
        time_vars = list(filter(match, varkeys)) #list of matching netCDF Dataset variable names
        for name in reversed(time_vars):
            var = all_vars[name]
            # Check for a data match
            if np.array_equal(var[:], self.data): #got match if data arrays are equal element by element.
                return (name, True)

        #No match with existing netCDF Dataset variables.  Make name and return it.
        if len(time_vars) == 0:
            name = period_name
        else:
            name = period_name + str(len(time_vars))

        return (name, False)


    def get_stride(self, as_timedelta=False):
        """Returns the number of seconds between the end times of two successive periods."""

        #Determine the stride.
        sample_data = self.data.flatten()
        loc = np.where(sample_data != FILL_VALUE)
        if len(loc[0]) < 4:
            raise IndexError("PhenomenonTimePeriod data has only 1 or 0 periods.")
        stride = int(sample_data[loc[0][3]]-sample_data[loc[0][1]])

        #Return stride as timedelta object as requested in setting as_timedelta to True
        if as_timedelta:
            return timedelta(seconds=stride)

        return stride



class PhenomenonTime(Time):
    """Class representing the Phenomenon Time Instant.
    It is ostensibly the time at which a forecast is valid
    or a measurement is made.
    """

    def __init__(self, **kwargs):
        """Initializes the data array."""

        #Set natal name of PhenomenonTime object.  It may change during process.
        self.name = "OM__phenomenonTimeInstant"

        #Create PhenomenonTime data from required keyword arguments 'start_time' and 'end_time'
        #OR from ...
        if 'start_time' in kwargs and 'end_time' in kwargs:
            start_time = kwargs['start_time']
            end_time = kwargs['end_time']
            try:
                stride = kwargs['stride']
            except:
                stride = ONE_HOUR

            super(PhenomenonTime, self).__init__(start_time=start_time,
                                                 end_time=end_time,
                                                 stride=stride)

        #... required keyword argument 'data'.  Here, we force the inputted data into
        #a numpy.ndarray and apply various acceptance tests on it.
        elif 'data' in kwargs:
            super(PhenomenonTime, self).__init__()
            data = np.asarray(kwargs['data']) #Convert data type to numpy.ndarray

            #Ensure that the data is not empty.
            size = data.size
            assert(size >= 1), "PhenomenonTimeInstant data is empty.\n It should not be."

            #Ensure that the data is one-dimensional.
            shape = data.shape
            ndims = len(shape)
            assert(ndims < 3), \
                "PhenomenonTimeInstant data is %r-dimensional.\n It should be <3-dimensional." % ndims

            #Ensure that there is at least one valid entry.
            i_valid = np.where(data != FILL_VALUE)
            n_valid = len(i_valid[0])
            assert(n_valid > 0), "PhenomenonTimeInstant data does not have a valid entry."

            #Refer the successfully create/tested data to the PhenomenonTime object.
            self.data = data

        self.metadata.update({ 'PROV__specializationOf' : '( OM__phenomenonTime )' })


    def get_dimensions(self):
        """Return a tuple of dimension names.
        Will account for data with different shapes.
        """

        #NOTE: What do the dimensions here say about the creation of data in __init__
        num_dims = len(self.data.shape)
        if num_dims == 1:
            dim_tuple = (get_time_dim_name(),)
        elif num_dims == 2: # In the case of model data
            dim_tuple = (get_lead_dim_name(), get_time_dim_name())
        else:
            raise AssertionError("more than 2 dimensions describing time")

        #NOTE: This assertion seems unnecessary given the above code.
        #assert len(dim_tuple) == len(self.data.shape)

        return dim_tuple


    def get_index(self, num_seconds):
        """Returns index where the lead time data equals num_seconds.
        Only checks if the start bound is equal to the input argument.
        Throws error if multiple indicies are found or none are found.
        """

        if len(self.data.shape) == 2:
            indices = np.where(self.data[:,0] == num_seconds)
        else:
            indices = np.where(self.data == num_seconds)

        # indices is returned as tuple; extract first element
        indices = indices[0]
        if len(indices) == 0:
            raise ValueError("time not found in PhenomenonTime object.")
        if len(indices) > 1:
            raise ValueError("lead time found multiple times in PhenomenonTime object.")

        return indices[0]


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

        self.name = 'ValidTime'

        if 'start_time' in kwargs and 'end_time' in kwargs:
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
            self.data = np.array(kwargs.get('data'))
            offset = 0

        self.metadata['PROV__specializationOf'] = '( StatPP__concepts/TimeBoundsSyntax/BeginEnd OM2__Data/Time/ValidTime )'
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

        if len(self.data.shape) == 1:
            logging.error('ValidTime cannot have a shape of 1, \
                    since it\'s of type OM__TimePeriod')
            raise ValueError

        #NOTE: Shouldn't the order of these dimensions be switched.
        if len(self.data.shape) == 2:
            dim_tuple = (self.get_bounded_dimension_name(),
                         get_time_dim_name())
        elif len(self.data.shape) == 3:
            dim_tuple = (get_lead_dim_name(),
                         get_time_dim_name(),
                         self.get_bounded_dimension_name())

        assert len(dim_tuple) == len(self.data.shape)

        return dim_tuple


    def get_stride(self, as_timedelta=False):
        """Returns the number of seconds between two time steps.
        This function may provide misleading information if timesteps
        have an irregular step duration.
        """

        size = len(self.data)
        if size <= 1:
            raise IndexError("Time data has 1 or 0 elements")

        if len(self.data.shape) == 3:
            start = self.data[0][0][0]
            end = self.data[1][0][0]
        elif len(self.data.shape) == 2:
            start = self.data[0][0]
            end = self.data[0][1]
        else:
            sample_data = self.data.flatten()
            start = sample_data[0]
            end = sample_data[1]
        stride = end - start

        if as_timedelta:
            return timedelta(seconds=stride)

        return stride



class ResultTime(Time):
    """Class representing the Result time.
    The result time is when the result (analysis, forcast)
    became available to data consumers.
    Must be an instant in time.
    """

    def __init__(self, **kwargs): # start_time=None, end_time=None, stride=ONE_HOUR, result_time=None):
        """Initializes the data array"""

        self.name = 'OM__resultTime'

        if 'start_time' in kwargs and 'end_time' in kwargs:
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
            self.data = np.array(kwargs.get('data'))

        self.metadata['standard_name'] = 'time'

        if 'result_time' in kwargs:
            result_time = kwargs['result_time']
            self.append_result(result_time)


    def append_result(self, result_time):
        """Adds the Result Time."""

        # Used to ammend the result time data
        o_type = type(result_time)

        if result_time is None:
            # Return current time rounded to the next hour
            r = datetime.now() + timedelta(hours=1)
            r = datetime(year=r.year, month=r.month,day=r.day, hour=r.hour)
            self.data[:] = epoch_time(r)
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
        """Initializes the data array"""

        self.name = 'FcstRefTime'

        if 'start_time' in kwargs and 'end_time' in kwargs:
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
            self.data = np.array(kwargs.get('data'))
        else:
            raise Exception("More arguments needed in forecastReferenceTime constructor")

        self.metadata.update({'standard_name':'forecast_reference_time'})

        if 'reference_time' in kwargs:
            self.append_reference_time(kwargs['reference_time'])

        self.metadata['PROV__specializationOf'] = '( StatPP__Data/Time/FcstRefTime )'


    def get_index(self, num_seconds):
        """Returns index where the forecastReferenceTime data equals num_seconds.
        Only checks if the start bound is equal to the input argument.
        Throws error if multiple indicies are found or none are found.
        """

        indices = np.where(self.data == num_seconds)

        # indices is returned as tuple; extract first element
        indices = indices[0]
        if len(indices) == 0: #NOTE: how does this jibe with the previous line
            raise ValueError("time not found in ForecastReferenceTime object.")
        if len(indices) > 1:
            err_str = "Found multiple desired times in ForecastReferencTime object."
            logging.info(err_str)
            raise ValueError(err_str)

        return indices[0]


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
        """Initializes the data array"""

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

            # Add PeriodicTime to metadata
            if len(self.data) > 1:
                first = self.data[0]
                duration = self.data[1] - self.data[0]
                last = self.data[-1]

                self.metadata['firstLeadTime'] = 'P' + str(int(first/60/60)) + 'H'
                self.metadata['PeriodicTime'] = 'P' + str(int(duration/60/60)) + 'H'
                self.metadata['lastLeadTime'] = 'P' + str(int(last/60/60)) + 'H'

        self.metadata.update({ 'standard_name' : "forecast_period" })
        self.metadata.update({ 'PROV__specializationOf' : '( StatPP__Data/Time/LeadTime )' })


    def get_dimensions(self):
        """Return a tuple of dimension names.
        Will account for data with different shapes.
        """

        dim_tuple = (get_lead_dim_name(),)
        assert len(dim_tuple) == len(self.data.shape)

        return dim_tuple


    def get_index(self, num_seconds):
        """Returns index where the lead time data equals num_seconds.
        Throws error if multiple indicies are found or none are found.
        """

        indices = np.where(self.data == num_seconds)
        # indices is returned as tuple; extract first element
        indices = indices[0]
        if len(indices) == 0:
            raise ValueError("lead time not found in LeadTime object.")
        if len(indices) > 1:
            raise ValueError("lead time found multiple times in LeadTime object.")

        return indices[0]


    def add_common_metadata(self, nc_var):
        """Adds metadata that is common to LeadTime variables."""

        #setattr(nc_var, 'calendar', 'gregorian')
        setattr(nc_var, 'units', 'seconds')
        setattr(nc_var, 'standard_name', 'time')


    def __add__(self, other):
        """In overloading the '+' operator in the other
        Time classes, it is assumed that the operation is
        done for a given lead time over the default time
        coordinate (days).  There is no reason to add the
        same lead time, so 'pass' is used to skip this operation,
        particularly the inherited operation from the
        parent class Time.  This explanation is longer than
        the code.
        """

        pass


    def __str__(self):
        """Format of response to typing the lead time object's name."""

        ret_str = "** " + self.name + " **" + "\n"
        ret_str += "Number of lead times: \n"
        ret_str += str(len(self.data)) + "\n"
        ret_str += "Data:\n"
        if len(self.data) > 6:
            for i in range(3):
                ret_str += str(int(self.data[i]/3600))
                ret_str += "hr,\n"
            ret_str += "   ...\n"
            for i in range(-3,0):
                ret_str += str(int(self.data[i]/3600))
                ret_str += "hr,\n"
        return ret_str


    __repr__ = __str__



def fast_arr_equal(arr1, arr2):
    """Determines if two arrays are equal.
    Confidence is low that they are indeed equal
    """

    len_arr1 = len(arr1)
    len_arr2 = len(arr2)
    if len_arr1 != len_arr2:
        return False

    first_eq = arr1[0] == arr2[0]
    last_eq = arr1[-1] == arr2[-1]

    return first_eq and last_eq
