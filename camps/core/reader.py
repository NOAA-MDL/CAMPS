import os
import numpy as np
from netCDF4 import Dataset
import pdb
import logging
import copy

from . import Time
from .Camps_data import Camps_data
from .Process import Process
from .Location import Location
from ..registry import constants as const


"""Module: reader.py

Methods:
    read
    read_var
    get_var
    get_location
    subset_time
    create_time
    get_procedures
    get_times
    get_coordinate
    removeTime
    get_metadata
    parse_list_attribute_string
"""


ancil_name = 'ancillary_variables'
file_cache = {}

def read(*filenames):
    """This function reads the netCDF4 files in an inputted list and
    creates a list of camps data objects, where each camps data object
    corresponds to a read netCDF4 primary variable.

    For data variables, the method read_var is called to create the objects
    and populate the metadata and data. Coordinate variables are created and
    populated seperately.

    Args:
        *filenames (list of str): list of paths to source netCDF4 files

    Returns:
        camps_data (list of :obj:Camps_data) : list of camps data objects
    """

    camps_data = []

    variables_dict = {}
    for filename in filenames:
        nc = Dataset(filename, mode='r', format="NETCDF4")
        variables_dict = nc.variables

        primary_list = nc.primary_variables.split()
        nc.close()
        for var_name in primary_list:
            if var_name in ['x','y','latitude','longitude','station'] or 'grid' in var_name:
                w_obj = Camps_data(var_name)
                w_obj.data = nc.variables[var_name][:]
                w_obj.dimensions = nc.variables[var_name].dimensions
                camps_data.append(w_obj)
                continue
            w_obj = read_var(filename,name=var_name)
            camps_data.append(w_obj)

    return camps_data


def read_var(filepath, name=None, lead_time=None, forecast_time=None, retrieve_mult=False, **metadata_dict):
    """Constructs and returns a Camps_data object of a primary netCDF4 variable.
    The variable data will be sliced at lead and forecast reference times if
    specified.

    Args:
        filepath (str): Filepath to source netCDF4 file.
        name (str): Exact name of primary netCDF4 variable.
        lead_time (optional, int): lead time in seconds associated with variable.
            Can subset data by its value.  Relevant only for forecast variables.
        forecast_time (optional, int): forecast reference time in epoch seconds.
            Can subset data by its value.
        retrieve_mult (optional, bool): whether retrieval of multiple variables is allowed.
            If set to False and multiple variables are retrieved, will result in an error.

    Returns:
        w_obj (Camps_data)
    """

    #Handle caching of the filehandle, so you don't need to open/close many times.
    if filepath in file_cache:
        nc = file_cache[filepath]['filehandle']
    else:
        nc = Dataset(filepath, mode='r', format="NETCDF4")
        file_cache[filepath] = {'filehandle':nc}

    if name is None: nc_vars = get_var(nc, metadata_dict)
    else: nc_vars = [nc.variables[name]]

    if nc_vars is None: return None
    if len(nc_vars)==0: return None
    elif len(nc_vars)>1 and retrieve_mult!=True:
        logging.error("more than 1 variable returned in get_var. Check desired metadata")
        raise ValueError
    w_objs = []
    for nc_var in nc_vars:
        logging.info("Retrieving "+nc_var.name) 
        #If lead_time is not None then it needs to be in seconds here
        if lead_time is not None:
            lead_time = lead_time*3600

        ancil_vars = nc_var.getncattr(ancil_name).split(' ')
        aux_coord_vars = nc_var.getncattr(const.COORD).split(' ')

        name = nc_var.getncattr("SOSA__observedProperty")
        w_obj = Camps_data(name, autofill=False)

        #Fill metadata dictionary
        metadata_exceptions = ['_FillValue']
        metadata_keys = nc_var.ncattrs()
        for key in metadata_keys:
            if key not in metadata_exceptions:
                value = nc_var.getncattr(key)
                w_obj.add_metadata(key, value)

        #Fill in list of preprocesses from two sources: the read variable's
        #preprocesses and processes
        try:
            p_string = nc_var.getncattr('PROV__wasInformedBy')
            procedures = parse_list_attribute_string(p_string)
            for ip, p in enumerate(procedures):
                p = str(p)
                w_obj.add_preprocess(p)
                attributes = nc.variables[p].ncattrs()
                for attr in attributes:
                    if attr not in list(w_obj.preprocesses[ip].attributes.keys()):
                        w_obj.preprocesses[ip].add_attribute(attr, nc.variables[p].getncattr(attr))
        except AttributeError:
            pass
        p_string = nc_var.getncattr('SOSA__usedProcedure')
        procedures = parse_list_attribute_string(p_string)
        for ip, p in enumerate(procedures):
            p = str(p)
            w_obj.add_preprocess(p)
            attributes = nc.variables[p].ncattrs()
            for attr in attributes:
                if attr not in list(w_obj.preprocesses[ip].attributes.keys()):
                    w_obj.preprocesses[ip].add_attribute(attr, nc.variables[p].getncattr(attr))

        #Grab the netCDF4 time variables and then, create and insert time
        #objects into the camps data object.
        t_names = []
        for v in ancil_vars:
            if 'Time' in v or '_time' in v:
                nc_time = nc.variables[v]
                t_obj = create_time(nc_time, lead_time, forecast_time)
                w_obj.time.append(t_obj)
                t_names.append(t_obj.name)

        #Check if lead_time is in the LeadTime object for a forecast
        #netCDF4 variable.  But first check if forecast reference time exists.
        #If either do not, return None.
        if forecast_time is not None and w_obj.is_model():
            i = t_names.index('FcstRefTime')
            if isinstance(forecast_time,list):
                j = np.where(np.isin(w_obj.time[i].data[:],forecast_time))[0]
                if len(j)==0:
                    logging.info("Specified forecast reference times not found.")
                    return None
            else:
                try:
                    j = list(w_obj.time[i].data[:]).index(forecast_time)
                except ValueError:
                    logging.info("Specified forecast reference time not found.")
                    return None
            if lead_time is not None:
                i = t_names.index('lead_times')
                try:
                    j = list(w_obj.time[i].data[:]).index(lead_time)
                except ValueError:
                    logging.info("Specified lead time not found")
                    return None

        #Get coordinates
        coord_vars = []
        try:
            coord_vars = [x.strip(' ') for x in nc_var.getncattr('coordinates').split(' ')]
        except:
            pass # No coordinate attribute in nc_var

        #Get locations, be it stations or gridpoints.
        location = get_location(filepath, nc, coord_vars)
        w_obj.location = location
        #Fill out the camps data objects properties dictionary.
        try:
            nc_coord = nc.variables[w_obj.vertical_coord]
        except:
            logging.warning("can't find vertical coordinate information for " + w_obj.name)
        try: #first treat as bounded level, will error out if it is a single level
            w_obj.properties['coord_val1'] = np.array(nc_coord[:].data[0][0])
            w_obj.properties['coord_val2'] = np.array(nc_coord[:].data[0][1])
        except: #if it is not bounded then it is a single level
            w_obj.properties['coord_val'] = nc_coord[0]

        #If 'hours' is an attribute of the netCDF4 variable,
        #insert its key/value pair into the properties dictionary
        #of the camps data object.
        if 'hours' in metadata_keys:
            value = nc_var.getncattr('hours')
            w_obj.properties['hours'] = value

        #'leadtime' is an attribute of a forecast netCDF4 variable.
        #Insert its key/value pair into the properties dictionary
        #of the camps data object.
        if 'leadtime' in metadata_keys:
            value = nc_var.getncattr('leadtime')
            w_obj.properties['reserved2'] = value
        #----------------------------------------------------------------------------------------

        #Add Dimensions.  Must be added before the data is added.
        w_obj.dimensions = list(nc_var.dimensions) #change to list so we can edit this

        #Store the netCDF4 variable data.  If lead time or forecast reference time exist,
        #slice along that time before storing in the camps data object.
        if lead_time is None and forecast_time is None:
            w_obj.data = nc_var[:]
        else:
            w_obj = subset_time(w_obj, nc_var, lead_time, forecast_time)

        w_objs.append(w_obj)

    if len(w_objs)==1: return w_objs[0]
    elif len(w_objs)>1 and retrieve_mult==True: return w_objs



# Function to retrieve a desired variable based on supplied metadata
def get_var(nc, metadata_dict):
    """ Retrieve variables from netcdf dataset object (nc) based on supplied
    metadata (metadata_dict).
    """

    if 'vert_coord2' not in metadata_dict.keys():
        levs = nc.get_variables_by_attributes(units=metadata_dict['vert_units'],axis='Z')
        levs = [lev for lev in levs if lev.size==1]
        levs = [lev.name for lev in levs if lev[:]==metadata_dict['vert_coord1']]
    else:
        levs = nc.get_variables_by_attributes(units=metadata_dict['vert_units'],axis='Z',long_name='pressure layer bounds')
        levs = [lev.name for lev in levs if lev[0,0]==metadata_dict['vert_coord1'] and lev[0,1]==metadata_dict['vert_coord2']]

    # Construct a coordinate attribute string based on determined level and whether desired variable is grid or station data
    if len(levs)==0: return None
    elif len(levs)>1:
        logging.error("more than 1 level returned in get_var. Check desired metadata.")
        raise ValueError
    vert_coord = levs[0]

    # Create dictionary to populate with search criteria for get_variables_by attributes function
    variable_search_dict = {}
    variable_search_dict['SOSA__observedProperty'] = metadata_dict['property']
    variable_search_dict[const.VERT_COORD] = vert_coord
    if 'reserved2' in metadata_dict.keys():
        variable_search_dict['leadtime'] = metadata_dict['reserved2']

    # Search for desired variable based on the observed Property, the coordinates, and the duration.
    #if 'duration_method' in metadata_dict.keys():
    #    variable_search_dict['hours']=metadata_dict['duration']
    #    variable_search_dict['cell_methods']='default_time_coordinate_size: '+metadata_dict['duration_method']
    #    potential_variables = nc.get_variables_by_attributes(**variable_search_dict)
    #else
    #    potential_variables = nc.get_variables_by_attributes(**variable_search_dict)
    #    potential_variables = [v for v in potential_variables if 'instant' in v.name]
    if 'duration' in metadata_dict.keys():
        if metadata_dict['duration']!=0:
            variable_search_dict['hours']=metadata_dict['duration']
            variable_search_dict['cell_methods']='phenomenonTime: '+metadata_dict['duration_method']
            potential_variables = nc.get_variables_by_attributes(**variable_search_dict)
        elif metadata_dict['duration']==0:
            potential_variables = nc.get_variables_by_attributes(**variable_search_dict)
            potential_variables = [v for v in potential_variables if 'instant' in v.name]
    else:
        potential_variables = nc.get_variables_by_attributes(**variable_search_dict)
    potential_variables = [var for var in potential_variables if var.name in nc.getncattr('primary_variables').split()]
    return potential_variables


def get_location(filename, nc, coord_vars):
    """Create a location object for a camps data object from
    the location information in a netCDF4 file.
    """
    if file_cache[filename] and 'location' in file_cache[filename]:
        return copy.copy(file_cache[filename]['location'])

    locations = []
    for c in coord_vars:
        if 'time' in c or 'Time' in c: continue
        try:
            nc_coord = nc.variables[c]
        except:
            logging.warning("can't find " + str(c))
            continue
        coord_len = len(nc_coord[:])
        if coord_len > 2: # location data
            locations.append(nc_coord)
            if 'stations' in nc_coord.dimensions:
                add_coord = nc.variables['stations']
                if add_coord not in locations:
                    locations.append(add_coord)
            

    location_obj = Location(*locations)
    if location_obj.location_data:
        file_cache[filename]['location'] = copy.copy(location_obj)

    return location_obj


def subset_time(w_obj, nc_var, lead_time, time):
    """Slice the data to specified lead times or forecast reference times for
    a forecast variable or to phenomenon time for observation variable.
    Adjust the time objects data accordingly.

    Args:
        w_obj (:obj:`Camps_data`): Camps_object to store the data.
                Assumes w_obj has Time compositions>
        nc_var (obj:`NetCDF4.Dataset.Variable`): netCDF4 variable where data is subset from.
        lead_time (int): lead time to subset.
        time (int): forecast or phenomenon time to subset

    Returns:
        w_obj (:obj:`Camps_data`): same reference(!) to the input w_obj but with the
            data reduced along specific times and time objects modified accordingly.
            This return is not necessary.
    """

    #Lead time is a parameter of model data only.
    #First, check if it's model data. If it is not and
    #lead time was requested, throw warning and return
    if not w_obj.is_model() and lead_time is not None:
        logging.warning("Attempt was made to subset by lead_time on non-model data")
        w_obj.data = nc_var[:]
        return w_obj

    #Initialize lead time index and phenomenon (or forecast reference) time index for slicing.
    l_time_index = None
    p_time_index = None
    #Search lead time variable for proper index
    if lead_time is not None:
        l_time = w_obj.get_lead_time()
        l_time_index = l_time.get_index(lead_time)
        #Get rid of lead_time dimension in object
        index = [i for i, s in enumerate(w_obj.dimensions) if 'lead_time' in s]
        w_obj.dimensions.pop(index[0])

    #Search forecast reference time variable for proper index for a forecast variable
    #and pop that dimension out of the camps data objects dimension attribute.
    if time is not None and w_obj.is_model():
        p_time = w_obj.get_forecast_reference_time()
        p_time_index = p_time.get_index(time)
    #Search phenomenon time variable for proper index for an observed variable
    elif time is not None and w_obj.is_vector():
        p_time = w_obj.get_phenom_time()
        p_time_index = p_time.get_index(time)

    if w_obj.is_model() and w_obj.is_vector():
        if p_time_index is not None:
            data = nc_var[:][p_time_index,:]
    elif w_obj.is_model():
        if l_time_index is not None and p_time_index is not None:
            data = nc_var[:][p_time_index,l_time_index,:,:]
        elif l_time_index is not None:
            data = nc_var[:][:,l_time_index,:,:]
        elif p_time_index is not None:
            data = nc_var[:][p_time_index,:,:,:]
    elif w_obj.is_vector():
        data = nc_var[:][p_time_index,:]
    w_obj.data = data

    # Subset the time objects
    for t in w_obj.time:
        #Initialize slice array
        slice_arr = [slice(None)]*t.data.ndim
        dimensions =  t.get_dimensions()

        if 'lead_times' in dimensions and lead_time is not None:
            lead_time_index = dimensions.index('lead_times')
            slice_arr[lead_time_index] = slice(l_time_index, l_time_index+1)

        if 'phenomenonTime' in dimensions and time is not None:
            fcst_time_index = dimensions.index('phenomenonTime')
            if len(p_time_index)>1:
                slice_arr[fcst_time_index] = slice(p_time_index[0],p_time_index[-1]+1,np.diff(p_time_index)[0])
            else:
                slice_arr[fcst_time_index] = slice(p_time_index[0], p_time_index[-1]+1)

        if t.name == 'phenomenonTimes':
            t.data = t.data[slice_arr].ravel()
        else:
            t.data = t.data[slice_arr]

    return w_obj #this return is not necessary.


def create_time(nc_variable, lead_time=None, fcst_time=None):
    """Create a Time object for the camps data object from a netCDF4 time variable.

    Args:
        nc_variable (:obj:`NetCDF4.Dataset.Variable`): netCDF4 time variable
        lead_time (int, optional): lead time of netCDF4 variable in seconds.
        fcst_time (int, optional): forecast reference times of netCDF4 variable
            in epoch seconds.

    Returns:
        t_obj (:obj:(`Time` subclass): subclass of Time with appropriate data.
    """

    time_switch = {
            'SOSA__phenomenonTime' : Time.PhenomenonTime,
            'phenomenonTimePeriod' : Time.PhenomenonTimePeriod,
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
    if 'Period' in nc_variable.name and t_class==Time.PhenomenonTime: t_class=Time.PhenomenonTimePeriod
    t_obj =  t_class(data=nc_variable[:])

    #add metadata to the time object
    attributes = nc_variable.ncattrs()
    for a in attributes:
        value = nc_variable.getncattr(a)
        if a == 'period':  #obj needs attribute duration of it is a duration variable
            t_obj.duration = value
        else:
            t_obj.metadata[a] = value

    return t_obj



def get_procedures(nc_variable, procedures_dict):
    """Returns the netcdf variables associated with SOSA__usedProcedure.

    Args:
        nc_variable (:obj:`NetCDF4.Dataset.Variable`): variable to extract procedures.
        procedures_dict (dict): dict containing procedure Variables.

    Returns:
        (:obj:list of :obj:`NetCDF4.Dataset.Variable`): Procedures from Variable.
    """

    #Grab the procedures listed for the variable in the netCDF4 file
    try:
        p_string = nc_variable.getncattr('SOSA__usedProcedure')
    except AttributeError:
        logging.warning(str(nc_variable))
        return None
    procedures = parse_list_attribute_string(p_string)

    #Construct a list of procedures and return it.
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
        time_vars (list): List of time objects for camps data object.
    """

    time_vars = []

    #Get the value of PhenomenonTime in time_dict
    try:
        time = nc_variable.getncattr('PhenomenonTime')
        try:
            time_vars.append(time_dict[time])
        except:
            logging.warning("time not in NetCDF file")
    except:
        #no phenomenonTime
        pass

    #Get value of ValidTime in time_dict
    try:
        time = nc_variable.getncattr('ValidTime')
        try:
            time_vars.append(time_dict[time])
        except:
            logging.warning("time not in NetCDF file")
    except:
        #no validTime
        pass

    #Get value of ForecastReferenceTime in time_dict
    try:
        time = nc_variable.getncattr('ForecastReferenceTime')
        try:
            time_vars.append(time_dict[time])
        except:
            logging.warning("time not in NetCDF file")
    except:
        #no ForecastReferenceTime
        pass

    #Get value of ResultTime in time_dict
    try:
        time = nc_variable.getncattr('ResultTime')
        try:
            time_vars.append(time_dict[time])
        except:
            logging.warning("time not in NetCDF file")
    except:
        #no resultTime
        pass

    #Get value of LeadTime in time_dict
    try:
        time = nc_variable.getncattr('LeadTime')
        try:
            time_vars.append(time_dict[time])
        except:
            logging.warning("time not in NetCDF file")
    except:
        #no leadTime
        pass

    return time_vars


def get_coordinate(nc_variable, coordinate_dict):
    """Returns the netcdf variable for the coordinate of the given
    variable if it exists.

    Args:
        nc_variable (:obj:`NetCDF4.Dataset.Variable`): Variable to extract coordinate.
        coordinate_dict (dict of Variables):

    Returns:
        Variable associated with coordinate or None if coordinate empty.
    """

    try:
        coord_name = nc_variable.getncattr("coordinates")
        try:
            return coordinate_dict[coord_name]
        except:
            logging.warning("coord_name not in nc file")
    except:
        return None  # no coordinate


def removeTime(attrs):
    """Removes Time metadata from a list of attributes.

    Args:
        attrs (:list: of str): a list of attributes
    """

    attrs_cp = attrs[:]
    for i in attrs_cp:
        if 'Time' in i:
            attrs.remove(i)

    return attrs #return is unnecessary


def get_metadata(nc_variable):
    """Gets metadata from netCDF4 variable.

    Args:
        nc_variable (:obj:NetCDF.Dataset.Variable):

    Returns:
        metadata (dict): Representation of metadata.
    """

    attributes = nc_variable.ncattrs()
    attributes = removeTime(attributes)

    metadata = {}
    for a in attributes:
        attr = nc_variable.getncattr(a)
        metadata[a] = attr

    return metadata


def parse_list_attribute_string(process_string):
    """Splits a string listing processes into a list of process names
    that is returned.

    Args:
        process_string (str): Formatted process string; space separated
                enclosed in parens.

    Returns:
        (:list: of str): list of only the process names
    """

    #Return empty list if input string consists of a space bracketed
    #by parentheses.
    if process_string.strip() == '( )':
        return []

    #Cull the bracketing parentheses and split the string into a list
    #of terms to be returned.
    process_string = process_string.replace("( ", "")
    process_string = process_string.replace(" )", "")
    processes = process_string.split(' ')
    if not processes[0]: #Return empty list if no terms
        return []

    return processes

