import os
from netCDF4 import Dataset
from Wisps_data import Wisps_data
import Time
from Process import Process
import pdb
from Location import Location
import logging
logging.basicConfig(level=logging.INFO)


ancil_name = 'ancillary_variables'
file_cache = {}

def read(*filenames):
    """Function to read a netCDF file of given
    filename into a list of WISPS data objects.
    Args:
        *filenames (:obj:list of str): netCDF files to pull from.
    
    Returns:
        (:obj:`list` of :obj:Wisps_data) : Wisps_data objects

    """
    wisps_data = []
    variables_dict = {}
    for filename in filenames:
        nc = Dataset(filename, mode='r', format="NETCDF4")
        variables_dict = nc.variables

        # Separates netCDF Variables into the metadata variables
        # and the predictor variables.
        procedures, variables_dict = separate_procedure_and_data(
            variables_dict)
        teimes, variables_dict = separate_time_and_data(variables_dict)
        coordinates, variables_dict = separate_coordinate_and_data(
            variables_dict)
        # Initializes the Wisps_data objects
        for v in variables_dict.values():
            w_obj = create_wisps_data(v, procedures, times, coordinates)
            wisps_data.append(w_obj)
    return wisps_data


def add_metadata_from_netcdf_variable(nc_var, wisps_obj):
    """Fill metadata dict in wisps object with relavent 
    metadata from the netcdf variable.
    Modifies given Wisps_object.
    Args:
        nc_var (:obj:Dataset.Variable): netCDF4 Dataset variable to pull metadata.
        wisps_obj (:obj:Wisps_data): Wisps_data object to add metadata.
    
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
    Returns a Wisps_data object from netcdf file. Optionally
    returns Wisps_data object with only a slice of data.
    Args:
        filepath (str): Filepath to netCDF file>
        name (str): Exact name of netCDF variable.
        lead_time (optional, int): lead time to subset. (seconds)
        forecast_time (optional, int): Time that forecast was made
                        in which to subset. (seconds)
    
    Returns:
        `obj`(Wisps_data)

    """
    if filepath in file_cache:
        nc = file_cache[filepath]['filehandle']
    else:
        nc = Dataset(filepath, mode='r', format="NETCDF4")
        file_cache[filepath] = {'filehandle':nc}
    nc_var = nc.variables[name]
    ancil_vars = nc_var.getncattr(ancil_name).split(' ')
    name = nc_var.getncattr("OM_observedProperty")
    w_obj = Wisps_data(name, autofill=False)

    # Fill metadata dict
    metadata_exceptions = ['_FillValue']
    metadata_keys = nc_var.ncattrs()
    for key in metadata_keys:
        if key not in metadata_exceptions:
            value = nc_var.getncattr(key)
            w_obj.add_metadata(key, value)
    # Get Processes
    p_string = nc_var.getncattr('OM_procedure')
    procedures = parse_processes_string(p_string)
    for p in procedures:
        w_obj.add_process(str(p))

    # Get Time
    time = []
    for v in ancil_vars:
        if 'Time' in v or '_time' in v:
            nc_time = nc.variables[v]
            t_obj = create_time(nc_time, lead_time, forecast_time)
            w_obj.time.append(t_obj)
            
    # Get vertCoord
    coord_vars = []
    try:
        coord_vars = [x.strip(' ') for x in nc_var.getncattr('coordinates').split(',')]
    except:
        pass # No coordinate attribute in nc_var

    location = get_location(filepath, nc, coord_vars)
    w_obj.location = location
    for c in coord_vars:
        nc_coord = nc.variables[c]
        coord_len = len(nc_coord[:])
        if coord_len <= 0:
            continue
        elif coord_len == 1: # Single level
            w_obj.properties['coord_val'] = nc_coord[0]
        elif coord_len == 2: # Bounded level
            w_obj.properties['coord_val1'] = nc_coord[0]
            w_obj.properties['coord_val2'] = nc_coord[1]

    
    # Add Dimensions
    w_obj.dimensions = nc_var.dimensions
    # Store data
    if lead_time is None and forecast_time is None:
        w_obj.data = nc_var[:]
    else:
        w_obj = subset_time(w_obj, nc_var, lead_time, forecast_time)
#    return (var,w_obj)
    return w_obj

def get_location(filename, nc, coord_vars):
    """
    """
    if file_cache[filename] and 'location' in file_cache[filename]:
        return file_cache[filename]['location']
    locations = []
    for c in coord_vars:
        nc_coord = nc.variables[c]
        coord_len = len(nc_coord[:])
        if coord_len > 2: # location data
            locations.append(nc_coord)
    location_obj = Location(*locations)
    file_cache[filename]['location'] = location_obj
    return location_obj

def get_coordinate_names(nc_var):
    pass

def subset_time(w_obj, nc_var, lead_time, time):
    """Only pull a slice of data from the netcdf variable if only a portion of time.
    rework time objects to reflect the subset.
    Args:
        w_obj (:obj:`Wisps_data`): Wisps_object to store the data.
                Assumes w_obj has Time compositions>
        nc_var (obj:`NetCDF4.Dataset.Variable`): Variable where data is subset from.
        lead_time (int): lead time to subset.
        time (int): forecast time to subset
    
    Returns:
        *obj*Wisps_data

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
    if time is not None:
        p_time = w_obj.get_forecast_reference_time()
        p_time_index = p_time.get_index(time)

    if l_time_index is not None and p_time_index is not None:
        data = nc_var[:,:,l_time_index, p_time_index]
    elif l_time_index: 
        data = nc_var[:,:,l_time_index,:]
    elif p_time_index: 
        data = nc_var[:,:,:,p_time_index]

    w_obj.data = data
    return w_obj


def create_time(nc_variable, lead_time=None, fcst_time=None):
    """Given a netcdf4 variable, create Time representation.
    Args:
        nc_variable (:obj:`NetCDF4.Dataset.Variable`): variable with which to create times.
    
    Returns:
        :obj:(`Time` subclass) subclass of Time with appropriate data.

    """
    time_switch = {
            'OM_phenomenonTime' : Time.PhenomenonTime,
            'OM_validTime' : Time.ValidTime,
            'OM_resultTime' : Time.ResultTime,
            'forecast_reference_time' : Time.ForecastReferenceTime,
            'LeadTime' : Time.LeadTime,
            'time_bounds' : Time.BoundedTime
            }
    role = nc_variable.getncattr("wisps_role")
    t_class = time_switch[role]
    attributes = nc_variable.ncattrs()
    t_obj =  t_class(data=nc_variable[:])
    # set metadata
    for a in attributes:
        value = nc_variable.getncattr(a)
        t_obj.metadata[a] = value
    if 'lead_times' in nc_variable.dimensions:
        lead_time_index = nc_variable.dimensions.index('lead_times')
    fcst_time_index = nc_variable.dimensions.index('default_time_coordinate_size')
    empty_slice = [slice(None)]*t_obj.data.ndim
    l_time = w_obj.get_lead_time()
    l_time_index = l_time.get_index(lead_time)
    empty_slice

    return t_obj

def get_procedures(nc_variable, procedures_dict):
    """
    returns the netcdf variables associated with OM_procedure.
    Args:
        nc_variable (:obj:`NetCDF4.Dataset.Variable`): variable to extract procedures.
        procedures_dict (dict): dict containing procedure Variables.
    
    Returns:
        (:obj:list of :obj:`NetCDF4.Dataset.Variable`): Procedures from Variable.

    """
    try:
        p_string = nc_variable.getncattr('OM_procedure')
    except AttributeError:
        print nc_variable
        return None
    procedures = parse_processes_string(p_string)
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


def create_wisps_data(nc_variable, procedures_dict, time_dict, coord_dict):
    """Given the netCDF variable and any associated procedures,
    creates and returns a Wisps_data object
    Args:
        nc_variable (:obj:NetCDF4.Dataset.Variable): Variable to convert.
        procedures_dict (dict): All Procedures in Dataset
        time_dict (dict): All Time Variables in Dataset
        coord_dict (dict): All Coordinat Variables ind Dataset
    
    Returns:
        (:obj:`Wisps_data`) Resultant Dataset

    """
    procedures = get_procedures(nc_variable, procedures_dict)
    times = get_times(nc_variable, time_dict)
    coordinate = get_coordinate(nc_variable, coord_dict)

    # Try to get OM_observedProperty from the netCDF Variable.
    # Every nc variable should have it.
    OM_observedProperty = ""
    try:
        OM_observedProperty = nc_variable.OM_observedProperty
    except AttributeError:
        err_msg = "No OM_observedProperty metadata in " + nc_variable.name
        logging.error(err_msg)
        #temp
        pass
        #raise

    # Create the initial Wisps_object.
    name = os.path.basename(OM_observedProperty)
    w_obj = Wisps_data(name, autofill=False)
    w_obj.dimensions = nc_variable.dimensions
    w_obj.time = times
    w_obj.processes = procedures
    # Add Coordinate value(s)
    if coordinate is not None:
        coord_value = coordinate[:]
        if len(coord_value) == 2:  # Then it's a bounded value
            w_obj.properties['coord_val1'] = coord_value[0]
            w_obj.properties['coord_val2'] = coord_value[1]
        elif len(coord_value) == 1:
            w_obj.properties['coord_val'] = coord_value[0]
        else:
            logging.error("more than 2 coordinate values in array")
    else:
        logging.debug("no coord for %s", nc_variable.name)

    attributes = get_metadata(nc_variable)
    w_obj.metadata = attributes
    w_obj.add_data(nc_variable[:])

    # Note: When a Wisps_data obect is created, it automatically
    # adds known metadata for the variable. However, if the netCDF
    # variable read from the file has different attributes, they
    # will take precedence.

    # Add metadata attributes and Procedures from the read netCDF variable.
#    for a in attributes:
#        attr_value = nc_variable.getncattr(a)
#
#        # Treat OM_Procedure differently, because it will need
#        # to create Process objects for each procedure.
#        if a == 'OM_Procedure':
#            processes = parse_processes_string(attr_value)
#            for p in processes:
#                if p not in procedures_dict:
#                    print "ERROR:", p, "is not defined a procedure"
#                else:
#                    source = ""
#                    process_step = ""
#                    try:
#                        source = procedures_dict[p].source
#                    except:
#                        pass
#                    try:
#                        process_step = procedures_dict[p].Process_step
#                    except:
#                        pass
#                    new_process = Process(p, process_step, source)
#                    w_obj.add_process(new_process)
#        # Otherwise, add the attribute to metadata dictionary
#        else:
#            w_obj.add_metadata(a, attr_value)

    return w_obj


def parse_processes_string(process_string):
    """Returns a list of process names given a formatted string string.
    Args:
        process_string (str): Formatted process string; comma separated 
                enclosed in parens.
    
    Returns:
        (:list: of str): list of only the process names

    """
    process_string = process_string.replace(" ", "")
    process_string = process_string.replace("(", "")
    process_string = process_string.replace(")", "")
    processes = process_string.split(',')
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
    process_identifier = 'LE_ProcessStep'
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
    elev_identifier = 'plev'
    plev_identifier = 'elev'
    for name, var in variables_dict.iteritems():
        if elev_identifier in name or plev_identifier in name:
            coordinate_dict[name] = var
        else:
            var_dict[name] = var

    return (coordinate_dict, var_dict)


