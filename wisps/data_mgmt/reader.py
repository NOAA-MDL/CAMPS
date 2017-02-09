from netCDF4 import Dataset
from Wisps_data import Wisps_data
from Process import Process
import pdb

def read(filename, *more_files):
    """Function to read a netCDF file of given filename into a list of WISPS data objects
    """
    wisps_data = []
    nc = Dataset(filename, mode='r', format="NETCDF4")
    variables_dict = nc.variables 

    # Separates netCDF Variables in the procedures and the data carrying variables.
    procedures, variables = separate_procedure_and_data(variables_dict)

    # Initializes the Wisps_data objects
    for v in variables:
        w_obj = create_wisps_data(v, procedures)
        wisps_data.append(w_obj)
    return wisps_data
       
def create_wisps_data(nc_variable, procedures_dict):
    """Given the netCDF variable and any associated procedures, 
    creates and returns a Wisps_data object
    """
    # Try to get OM_observedProperty from the netCDF Variable. 
    # Every nc variable should have it.
    OM_observedProperty = ""
    try:
        OM_observedProperty = nc_variable.OM_observedProperty
    except AttributeError:
        print "ERROR: No OM_observedProperty metadata in ", nc_variable.name
        print "       Skipping variable"
    
    # Create the initial Wisps_object.
    w_obj = Wisps_data(nc_variable.name, OM_observedProperty)
    attributes = nc_variable.ncattrs()
    w_obj.add_data(nc_variable[:])

    # Note: When a Wisps_data obect is created, it automatically
    # adds known metadata for the variable. However, if the netCDF
    # variable read from the file has different attributes, they 
    # will take precedence.

    # Add metadata attributes and Procedures from the read netCDF variable.
    for a in attributes:
        attr_value = nc_variable.getncattr(a)

        # Treat OM_Procedure differently, because it will need
        # to create Process objects for each procedure.
        if a == 'OM_Procedure':
            processes = parse_processes_string(attr_value)
            for p in processes:
                if p not in procedures_dict:
                    print "ERROR:",p,"is not defined a procedure"
                else:
                    source = ""
                    process_step = ""
                    try:
                        source = procedures_dict[p].source
                    except:
                        pass
                    try:
                        process_step = procedures_dict[p].Process_step
                    except:
                        pass
                    new_process = Process(p, process_step, source)
                    w_obj.add_process(new_process)
        # Otherwise, add the attribute to metadata dictionary
        else: 
            w_obj.add_metadata(a, attr_value)

        return w_obj

def parse_processes_string(process_string):
    """Returns a list of process names given a string 
    that is comma separated and enclosed in parens.
    """
    process_string = process_string.replace(" ","")
    process_string = process_string.replace("(","")
    process_string = process_string.replace(")","")
    processes = process_string.split(',')
    return processes

def separate_procedure_and_data(variables_dict):
    """Separates the variables into Processes and data-holding variables. 
    Returns the processes and normal variables as a tuple.
    """
    process_identifier = 'process'
    process_dict = {}
    variable_list = []

    for var_name,variable in variables_dict.iteritems():
        if process_identifier in var_name:
            process_dict[var_name] = variable
        else:
            variable_list.append(variable)

    return (process_dict, variable_list)

            




