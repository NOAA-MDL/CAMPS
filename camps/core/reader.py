import os
import numpy as np
from netCDF4 import Dataset
import pdb
import logging

from . import Time
from Camps_data import Camps_data
from Process import Process
from Location import Location

ancil_name = 'ancillary_variables'
file_cache = {}

def read(*filenames):
    """Function to read a netCDF file of given
    filename into a list of CAMPS data objects.
    Args:
        *filenames (:obj:list of str): netCDF files to pull from.

    Returns:
        (:obj:`list` of :obj:Camps_data) : Camps_data objects

    """
    camps_data = []
    variables_dict = {}
    for filename in filenames:
        nc = Dataset(filename, mode='r', format="NETCDF4")
        variables_dict = nc.variables

        # Separates netCDF Variables into the metadata variables
        # and the predictor variables.
        procedures, variables_dict = separate_procedure_and_data(
            variables_dict)
        times, variables_dict = separate_time_and_data(variables_dict)
        coordinates, variables_dict = separate_coordinate_and_data(
            variables_dict)
        nc.close()
        # Initializes the Camps_data objects
        for varname,vardata in variables_dict.iteritems():
            logging.info("Reading "+str(varname))
            w_obj = read_var(filename, varname)
            camps_data.append(w_obj)

    return camps_data


def add_metadata_from_netcdf_variable(nc_var, camps_obj):
    """Fill metadata dict in camps object with relavent
    metadata from the netcdf variable.
    Modifies given Camps_object.
    Args:
        nc_var (:obj:Dataset.Variable): netCDF4 Dataset variable to pull metadata.
        camps_obj (:obj:Camps_data): Camps_data object to add metadata.

    Returns:
        None

    """
    metadata_exceptions = ['_FillValue']
    metadata_keys = nc_var.ncattrs()
    for key in metadata_keys:
        if key not in metadata_exceptions:
            value = nc_var.getncattr(key)
            w_obj.add_metadata(key, value)


def read_var(filepath, name, lead_time=None, forecast_time=None):
    """
    Returns a Camps_data object from netcdf file. Optionally
    returns Camps_data object with only a slice of data.
    Args:
        filepath (str): Filepath to netCDF file>
        name (str): Exact name of netCDF variable.
        lead_time (optional, int): lead time to subset. (seconds)
        forecast_time (optional, int): Time that forecast was made
                        in which to subset. (seconds)

    Returns:
        `obj`(Camps_data)

    """
    # Handle caching of the filehandle, so you don't need to open/close many times.
    #pdb.set_trace()    
    if filepath in file_cache:
        nc = file_cache[filepath]['filehandle']
    else:
        nc = Dataset(filepath, mode='r', format="NETCDF4")
        file_cache[filepath] = {'filehandle':nc}
    nc_var = nc.variables[name]

    # If lead_time is not None then it needs to be in seconds here
    if lead_time is not None:
        lead_time = lead_time*3600

    ancil_vars = nc_var.getncattr(ancil_name).split(' ')

    name = nc_var.getncattr("OM__observedProperty")
    w_obj = Camps_data(name, autofill=False)

    # Fill metadata dict
    metadata_exceptions = ['_FillValue']
    metadata_keys = nc_var.ncattrs()
    for key in metadata_keys:
        if key not in metadata_exceptions:
            value = nc_var.getncattr(key)
            w_obj.add_metadata(key, value)
    # Get Processes
    p_string = nc_var.getncattr('SOSA__usedProcedure')
    procedures = parse_list_attribute_string(p_string)
    for p in procedures:
        w_obj.add_process(str(p))

    # Get Time
    t_names = []
    for v in ancil_vars:
        if 'Time' in v or '_time' in v:
            nc_time = nc.variables[v]
            t_obj = create_time(nc_time, lead_time, forecast_time)
            w_obj.time.append(t_obj)
            t_names.append(t_obj.name)

    # Check if lead_time is in the LeadTime object.
    # But first check if forecast reference time exists.
    # If either do not, return None.
    if forecast_time is not None and w_obj.is_model():
        try:
            i = t_names.index('FcstRefTime')
            j = list(w_obj.time[i].data[:]).index(forecast_time)
        except ValueError:
            logging.info("Specified forecast reference time not found.")
            pdb.set_trace()
            return None
        if lead_time is not None:
            i = t_names.index('LeadTime')
            try:
                j = list(w_obj.time[i].data[:]).index(lead_time)
            except ValueError:
                logging.info("Specified lead time not found")
                return None

    # Get vertCoord
    coord_vars = []
    try:
        coord_vars = [x.strip(' ') for x in nc_var.getncattr('coordinates').split(' ')]
    except:
        pass # No coordinate attribute in nc_var

    location = get_location(filepath, nc, coord_vars)
    w_obj.location = location

    #This loop is over our coordinates list which is either [plev(elev), x, y] or [plev(elev), stations]
    #I don't see a reason to loop here.  If our level is always the first in the list then we can just 
    #access it directly.  I added an if statement just to be safe though.  Otherwise it messes up 
    #the bounded level variables.
    for c in coord_vars: #I don't think we need to be looping here.  Why would we need coord info on stations?
        if 'lev' in c: # Pick out the level from coordinate list
            try:
                nc_coord = nc.variables[c]
            except:
                logging.warning("can't find " + str(c))
                continue

            try: #first treat as bounded level, will error out if it is a single level
                w_obj.properties['coord_val1'] = np.array(nc_coord[:].data[0][0])
                w_obj.properties['coord_val2'] = np.array(nc_coord[:].data[0][1])
            except: #if it is not bounded then it is a single level
                w_obj.properties['coord_val'] = nc_coord[0]

    # Hours needs to be in properties...we may or may not need this in the end
    if 'hours' in metadata_keys: 
        value = nc_var.getncattr('hours')
        w_obj.properties['hours'] = value

    # If value has a lead time then we need to save that in reserved2 in properties 
    # so it can be added to the database later
    if 'leadtime' in metadata_keys:
        value = nc_var.getncattr('leadtime')
        w_obj.properties['reserved2'] = value

    # Add Dimensions
    w_obj.dimensions = list(nc_var.dimensions) #change to list so we can edit this
    # Store data
    if lead_time is None and forecast_time is None:
        w_obj.data = nc_var[:]
    else:
        w_obj = subset_time(w_obj, nc_var, lead_time, forecast_time)

    return w_obj

def get_location(filename, nc, coord_vars):
    """
    """
    if file_cache[filename] and 'location' in file_cache[filename]:
        return file_cache[filename]['location']
    locations = []
    for c in coord_vars:
        try:
            nc_coord = nc.variables[c]
        except:
            logging.warning("can't find " + str(c))
            continue
        coord_len = len(nc_coord[:])
        if coord_len > 2: # location data
            locations.append(nc_coord)
    location_obj = Location(*locations)
    if location_obj.location_data:
        file_cache[filename]['location'] = location_obj
    return location_obj


def subset_time(w_obj, nc_var, lead_time, time):
    """Only pull a slice of data from the netcdf variable if only a portion of time.
    rework time objects to reflect the subset.
    Args:
        w_obj (:obj:`Camps_data`): Camps_object to store the data.
                Assumes w_obj has Time compositions>
        nc_var (obj:`NetCDF4.Dataset.Variable`): Variable where data is subset from.
        lead_time (int): lead time to subset.
        time (int): forecast time to subset

    Returns:
        *obj*Camps_data

    """

    # First, check if it's model data. if it is not and
    # lead time was requested return obj, throw warning
    if not w_obj.is_model() and lead_time is not None:
        logging.warning("Attempt was made to subset by lead_time on non-model data")
        w_obj.data = nc_var[:]
        return w_obj

    l_time_index = None
    p_time_index = None
    # Next, search lead_time variable for proper index
    if lead_time is not None:
        l_time = w_obj.get_lead_time()
        l_time_index = l_time.get_index(lead_time)
        # Get rid of lead_time dimension in object
        index = [i for i, s in enumerate(w_obj.dimensions) if 'lead_time' in s]
        w_obj.dimensions.pop(index[0])
    if time is not None and w_obj.is_model():
        p_time = w_obj.get_forecast_reference_time()
        p_time_index = p_time.get_index(time)
        # Get rid of time dimension in object
        index = [i for i, s in enumerate(w_obj.dimensions) if 'default_time' in s]
        w_obj.dimensions.pop(index[0])
    elif time is not None and w_obj.is_vector():
        p_time = w_obj.get_phenom_time()
        p_time_index = p_time.get_index(time)
    if w_obj.is_model() and w_obj.is_vector():
        if p_time_index is not None:
            data = nc_var[p_time_index,:]
    elif w_obj.is_model():
        if l_time_index is not None and p_time_index is not None:
            #data = nc_var[:,:,l_time_index, p_time_index]
            data = nc_var[p_time_index,l_time_index,:,:]
        elif l_time_index is not None:
            #data = nc_var[:,:,l_time_index,:]
            data = nc_var[:,l_time_index,:,:]
        elif p_time_index is not None:
            #data = nc_var[:,:,:,p_time_index]
            data = nc_var[p_time_index,:,:,:]
    elif w_obj.is_vector():
        data = nc_var[p_time_index,:]

    w_obj.data = data
    # Next Subset the time objects
    for t in w_obj.time:
        # Initialize slice array
        slice_arr = [slice(None)]*t.data.ndim
        dimensions =  t.get_dimensions()
        if 'lead_times' in dimensions and lead_time is not None:
            lead_time_index = dimensions.index('lead_times')
            slice_arr[lead_time_index] = slice(l_time_index, l_time_index+1)
        if 'default_time_coordinate_size' in dimensions and time is not None:
            fcst_time_index = dimensions.index('default_time_coordinate_size')
            slice_arr[fcst_time_index] = slice(p_time_index, p_time_index+1)
        if t.name == 'OM__phenomenonTimeInstant':
            t.data = t.data[slice_arr].ravel()
        else:
            t.data = t.data[slice_arr]
    return w_obj


def create_time(nc_variable, lead_time=None, fcst_time=None):
    """Given a netcdf4 variable, create Time representation.
    Args:
        nc_variable (:obj:`NetCDF4.Dataset.Variable`): variable with which to create times.

    Returns:
        :obj:(`Time` subclass) subclass of Time with appropriate data.

    """
    time_switch = {
            'OM__phenomenonTime' : Time.PhenomenonTime,
            'OM__phenomenonTimePeriod' : Time.PhenomenonTimePeriod,
            'ValidTime' : Time.ValidTime,
            'OM__resultTime' : Time.ResultTime,
            'FcstRefTime' : Time.ForecastReferenceTime,
            'LeadTime' : Time.LeadTime
            }

    role = nc_variable.getncattr("PROV__specializationOf")
    if '(' and ')' in role:
        roles = parse_list_attribute_string(role)
        t_class = None
        for role in roles:
            role_bn = os.path.basename(role)
            if role_bn in time_switch:
                t_class = time_switch[role_bn]
        if t_class is None:
            raise Exception("Could not find defined class in role str: " + str(roles))
    t_obj =  t_class(data=nc_variable[:])
    # set metadata
    attributes = nc_variable.ncattrs()
    for a in attributes:
        value = nc_variable.getncattr(a)
        if a == 'period':  #obj needs attribute duration of it is a duration variable
            t_obj.duration = value
        else:
            t_obj.metadata[a] = value

    return t_obj

def reduce_time(time_objs):
    """
    """

    slice_arr = [slice(None)]*t_obj.data.ndim
    if 'lead_times' in nc_variable.dimensions:
        lead_time_index = nc_variable.dimensions.index('lead_times')
        slice_arr[lead_time_index] = None
    if 'default_time_coordinate_size' in nc_variable.dimensions:
        fcst_time_index = nc_variable.dimensions.index('default_time_coordinate_size')
        slice_arr[fcst_time_index ] = None

        t_obj.data.slice(empty_slice)

def get_procedures(nc_variable, procedures_dict):
    """
    returns the netcdf variables associated with SOSA__usedProcedure.
    Args:
        nc_variable (:obj:`NetCDF4.Dataset.Variable`): variable to extract procedures.
        procedures_dict (dict): dict containing procedure Variables.

    Returns:
        (:obj:list of :obj:`NetCDF4.Dataset.Variable`): Procedures from Variable.

    """
    try:
        p_string = nc_variable.getncattr('SOSA__usedProcedure')
    except AttributeError:
        logging.warning(str(nc_variable))
        return None
    procedures = parse_list_attribute_string(p_string)
    proc_list = []

    for p in procedures:
        logging.info("procedure name is " + p)
        try:
            proc = procedures_dict[p]
            proc_list.append(proc)
        except:
            logging.warning("procedure " + p + "not found in netcdf file")

    return proc_list


def get_times(nc_variable, time_dict):
    """Returns all the time variables associated with the nc_variable.
    Args:
        nc_variable (:obj:`NetCDF4.Dataset.Variable`): Variable to extract Times from.
        time_dict (dict of :obj:`Time`): Time objects from Variable

    Returns:
        None

    """
    time_vars = []
    try:
        time = nc_variable.getncattr('PhenomenonTime')
        try:
            time_vars.append(time_dict[time])
        except:
            loggin.warning("time not in NetCDF file")
    except:
        # no phenomenonTime
        pass
    try:
        time = nc_variable.getncattr('ValidTime')
        try:
            time_vars.append(time_dict[time])
        except:
            loggin.warning("time not in NetCDF file")
    except:
        # no validTime
        pass
    try:
        time = nc_variable.getncattr('ForecastReferenceTime')
        try:
            time_vars.append(time_dict[time])
        except:
            loggin.warning("time not in NetCDF file")
    except:
        # no ForecastReferenceTime
        pass
    try:
        time = nc_variable.getncattr('ResultTime')
        try:
            time_vars.append(time_dict[time])
        except:
            loggin.warning("time not in NetCDF file")
    except:
        # no resultTime
        pass
    try:
        time = nc_variable.getncattr('LeadTime')
        try:
            time_vars.append(time_dict[time])
        except:
            loggin.warning("time not in NetCDF file")
    except:
        # no leadTime
        pass

    return time_vars


def get_coordinate(nc_variable, coordinate_dict):
    """
    Returns the netcdf variable for the coordinate of the given
    variable if it exists.
    Args:
        nc_variable (:obj:`NetCDF4.Dataset.Variable`): Variable to extract coordinate.
        coordinate_dict (dict of Variables):

    Returns:
        Variable Associated with Coordinate or None if Coordinate empty.

    """
    try:
        coord_name = nc_variable.getncattr("coordinates")
        try:
            return coordinate_dict[coord_name]
        except:
            loggin.warning("coord_name not in nc file")
    except:
        return None  # no coordinate


def removeTime(attrs):
    """Removes Time metadata from attrs dict.
    Args:
        attrs ( ):

    Returns:
        None

    """
    attrs_cp = attrs[:]
    for i in attrs_cp:
        if 'Time' in i:
            attrs.remove(i)
    return attrs


def get_metadata(nc_variable):
    """gets metadata from variable.
    Args:
        nc_variable (:obj:NetCDF.Dataset.Variable):
    Returns:
        (dict): Representation of metadata.
    """
    attributes = nc_variable.ncattrs()
    attributes = removeTime(attributes)
    metadata = {}
    for a in attributes:
        attr = nc_variable.getncattr(a)
        metadata[a] = attr
    return metadata


def parse_list_attribute_string(process_string):
    """Returns a list of process names given a formatted string string.
    Args:
        process_string (str): Formatted process string; space separated
                enclosed in parens.

    Returns:
        (:list: of str): list of only the process names

    """
    if process_string.strip() == '( )':
        return []
    process_string = process_string.replace("( ", "")
    process_string = process_string.replace(" )", "")
    processes = process_string.split(' ')
    if not processes[0]:
        return []
    return processes


def separate_procedure_and_data(variables_dict):
    """Separates the variables into Processes and data-holding variables.
    Returns the processes and normal variables as a tuple.
    Args:
        variables_dict (dict of `Dataset.Variable`): Where name is the name
                of the nc variable, and the value is the Variable object

    Returns:
        (tuple): Where,
                index[0] are process variables dict.
                index[1] are the remainder of the variables.

    """
    #process_identifier = 'process'
    process_identifier = 'PROV__Activity'
    process_dict = {}
    var_dict = {}

    for var_name, variable in variables_dict.iteritems():
        #if process_identifier in var_name:
        if process_identifier in set(variable.ncattrs()):
            process_dict[var_name] = variable
        else:
            var_dict[var_name] = variable

    return (process_dict, var_dict)


def separate_time_and_data(variables_dict):
    """Separates the variables into Time and predictor variables.
    Returns the processes and normal variables as a tuple.
    Args:
        variables_dict (dict of `Dataset.Variable`): Where name is the name
                of the nc variable, and the value is the Variable object

    Returns:
        (tuple): Where,
                index[0] are Time variables dict.
                index[1] are the remainder of the variables.

    """
    time_dict = {}
    var_dict = {}
    time_identifiers = ['Time','time','begin_end_size']
    #time_identifier = 'Time'
    #time_identifier2 = 'time'
    matches_identifier = lambda i: i in name,
    for name, var in variables_dict.iteritems():
        for identifier in time_identifiers:
            if identifier in name:
                time_dict[name] = var
                break
        #if time_identifier in name or time_identifier2 in name:
        #    time_dict[name] = var
        else:
            var_dict[name] = var

    return (time_dict, var_dict)


def separate_coordinate_and_data(variables_dict):
    """Separates the variables into coordinate and predictor variables.
    Returns the processes and normal variables as a tuple.
    Args:
        variables_dict (dict of `Dataset.Variable`): Where name is the name
                of the nc variable, and the value is the Variable object

    Returns:
        (tuple): Where,
                index[0] are Coordinate variables dict.
                index[1] are the remainder of the variables.

    """
    coordinate_dict = {}
    var_dict = {}
    coord_identifiers = ['plev','elev', 'station','x','y','projection']
    elev_identifier = 'plev'
    plev_identifier = 'elev'
    station_identifier = 'station'

    for name, var in variables_dict.iteritems():
        if 'OM__observedProperty' not in var.ncattrs():
                coordinate_dict[name] = var
        else:
            var_dict[name] = var

    return (coordinate_dict, var_dict)
