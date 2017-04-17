import os
from netCDF4 import Dataset
from Wisps_data import Wisps_data
from Process import Process
import pdb
import logging
logging.basicConfig(level=logging.INFO)


def read(*filenames):
    """Function to read a netCDF file of given
    filename into a list of WISPS data objects.
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
        times, variables_dict = separate_time_and_data(variables_dict)
        coordinates, variables_dict = separate_coordinate_and_data(
            variables_dict)
        # Initializes the Wisps_data objects
        for v in variables_dict.values():
            w_obj = create_wisps_data(v, procedures, times, coordinates)
            wisps_data.append(w_obj)
    return wisps_data


def get_procedures(nc_variable, procedures_dict):
    """
    returns the netcdf variables associated with OM_procedure.
    """

    p_string = nc_variable.getncattr('OM_procedure')
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
    """
    time_vars = []
    try:
        time = nc_variable.getncattr('PhenomenonTime')
        try:
            time_vars.append(time_dict[time])
        except:
            loggin.warning("time Not in NC")
    except:
        # no phenomenonTime
        pass
    try:
        time = nc_variable.getncattr('ValidTime')
        try:
            time_vars.append(time_dict[time])
        except:
            loggin.warning("time Not in NC")
    except:
        # no validTime
        pass
    try:
        time = nc_variable.getncattr('ForecastReferenceTime')
        try:
            time_vars.append(time_dict[time])
        except:
            loggin.warning("time Not in NC")
    except:
        # no ForecastReferenceTime
        pass
    try:
        time = nc_variable.getncattr('ResultTime')
        try:
            time_vars.append(time_dict[time])
        except:
            loggin.warning("time Not in NC")
    except:
        # no resultTime
        pass
    try:
        time = nc_variable.getncattr('LeadTime')
        try:
            time_vars.append(time_dict[time])
        except:
            loggin.warning("time Not in NC")
    except:
        # no leadTime
        pass

    return time_vars


def get_coordinate(nc_variable, coordinate_dict):
    """
    Returns the netcdf variable for the coordinate of the given
    variable if it exists.
    """
    try:
        coord_name = nc_variable.getncattr("coordinate")
        try:
            return coordinate_dict[coord_name]
        except:
            loggin.warning("coord_name not in nc file")
    except:
        pass  # no coordinate


def removeTime(attrs):
    """Removes Time metadata from attrs dict.
    """
    attrs_cp = attrs[:]
    for i in attrs_cp:
        if 'Time' in i:
            attrs.remove(i)
    return attrs


def get_metadata(nc_variable):
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
        raise

    # Create the initial Wisps_object.
    name = os.path.basename(OM_observedProperty)
    w_obj = Wisps_data(name, autofill=False)
    w_obj.dimensions = nc_variable.dimensions
    w_obj.time = times
    w_obj.processes = procedures
    # Add Coordinate value(s)
    try:
        coord_value = coordinate[:]
        if len(coord) == 2:  # Then it's a bounded value
            w_obj.properties['coord_val1'] = coord_value[0]
            w_obj.properties['coord_val2'] = coord_value[1]
        elif len(coord) == 1:
            w_obj.properties['coord_val'] = coord_value[0]
        else:
            logging.error("more than 2 coordinate values in array")
    except:
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
    """Returns a list of process names given a string
    that is comma separated and enclosed in parens.
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
    """
    process_identifier = 'process'
    process_dict = {}
    var_dict = {}

    for var_name, variable in variables_dict.iteritems():
        if process_identifier in var_name:
            process_dict[var_name] = variable
        else:
            var_dict[var_name] = variable

    return (process_dict, var_dict)


def separate_time_and_data(variables_dict):
    """Separates the variables into Time and predictor variables.
    Returns the processes and normal variables as a tuple.
    """
    time_dict = {}
    var_dict = {}
    time_identifier = 'Time'
    time_identifier2 = 'time'
    for name, var in variables_dict.iteritems():
        if time_identifier in name or time_identifier2 in name:
            time_dict[name] = var
        else:
            var_dict[name] = var

    return (time_dict, var_dict)


def separate_coordinate_and_data(variables_dict):
    """Separates the variables into coordinate and predictor variables.
    Returns the processes and normal variables as a tuple.
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
