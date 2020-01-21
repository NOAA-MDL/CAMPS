import sys
import os
import logging
import inspect
import yaml
import pdb
"""
Module that abstracts the reading of
yaml configuration files held in config directory.
"""

CONFIG_PATH = os.path.dirname(os.path.realpath(__file__)) + "/"
_cache = {}


class nc_struct():
    def __init__(self):
        self.dimensions = {}
        self.global_attributes = {}
        self.variables = {}

class control_helper():
    """Allows for accessing yaml file variables via attribute
    or key.
    """
    raw_data = {}
    def __init__(self, kwargs):
        self.raw_data = kwargs
        for key,value in kwargs.iteritems():
            setattr(self,key,value)

    def __getitem__(self, key):
        return getattr(self,key)

def is_relative_path(path):
    """Returns true if string is a relative path and false if not"""
    if path[0] == '/':
        return False
    return True

def exists(path):
    """Returns whether path exists"""
    try:
        exists = os.stat(path)
    except os.error:
        return False
    return True

def get_config_path(path):
    """Get config path.
    Return absolute path if it's a relative path. Throw error if file/directory
    doesn't exist
    """
    # Construct full absolute path if it's relative
    if is_relative_path(path):
        path = CONFIG_PATH + path

    # Check if file exists
    if not exists(path):
        logging.critical("path: "+str(path)+" does not exist, or is a broken link")
        raise os.error

    return path

def read_yaml(filename):
    """Reads the contents of a yaml file and returns the value."""
    logging.info("reading yaml config. File: " + filename)
    try:
        with open(filename, 'r') as stream:
            try:
                structured_data = yaml.load(stream)
                if type(structured_data) is not dict:
                    return structured_data
                # If dict, allow for dict attrs to be accessed as attribute
                structured_data = control_helper(structured_data)
                return structured_data
            except yaml.YAMLError as err:
                logging.error("YAML cannot parse input")
                logging.error("Error:\n")
                logging.error(err)
                raise
    except IOError as err:
        logging.error(
            "File cannot be read. It may not exist, or cannot be read")
        logging.error("Error:" + str(err))
        raise


def read_cache():
    """checks whether the function's data has been cached or not.
    If it has, returns the values. otherwise, returns None.
    """
    func_name = inspect.currentframe().f_back.f_code.co_name
    try:
        return _cache[func_name]
    except KeyError:
        return None


def write_cache(data):
    """
    Caches data associated with calling function's name
    to prevent re-reading a file.
    """
    # Get the name of the function that called write_cache
    func_name = inspect.currentframe().f_back.f_code.co_name
    _cache[func_name] = data

def magic_strings():
    """Reads magic strings, or strings that have special meaning"""
    data = read_cache()
    if data:
        return data
    data = read_yaml(CONFIG_PATH + "keywords.yaml")
    write_cache(data)
    return data

def read_dimensions():
    """
    Reads and returns dimension definitions.
    """
    return read_nc_meta()['dimensions']


def read_globals():
    """
    Reads and returns global attributes definitions.
    """
    return read_nc_meta()['globals']


def read_prefixes():
    """
    Reads and returns global attributes definitions.
    """
    return read_nc_meta()['prefixes']


def read_variables():
    """
    returns structured configuration of all CAMPS supported variables.
    """
    return read_nc_meta()['variables']


def read_nc_meta():
    """Reads netcdf.yaml file that contains the metadata for
    common variables.
    """
    data = read_cache()
    if data:
        return data
    data = read_yaml(CONFIG_PATH + "netcdf.yaml")
    write_cache(data)
    return data

def read_procedures():
    """Reads procedures.yaml file that contains the metadata for
    procedures.
    """
    data = read_cache()
    if data:
        return data
    data = read_yaml(CONFIG_PATH + "procedures.yaml")
    write_cache(data)
    return data


def read_nc_config():
    """
    Read YAML config files to get netcdf structure and properties.
    """
    nc = nc_struct()
    nc.dimensions = read_dimensions()
    nc.global_attributes = read_globals()
    nc.variables = read_variables()
    return nc

def read_control(control_file=None):
    """
    Reads the any control file that provides time ranges and
    directory locations.
    """
    # Read file and put it in cache if control_file specified
    if control_file is not None:
        data = read_yaml(control_file)
        write_cache(data)
        return data
    #try to read the cache.
    else:
        data = read_cache()
        if data:
            return data
        else:
            # If no cached data or control file read return None  
            return None


def read_mospred_control(control_file=None):
    """
    Reads the metar control file that provides time ranges and
    directory locations for the observations.
    """
    # Read file and put it in cache if control_file specified
    if control_file is not None:
        data = read_yaml(control_file)
        write_cache(data)
        return data
    #Otherwise, try to read the cache.
    data = read_cache()
    if data:
        return data
    # If nothing cached, read default control file
    data = read_yaml(CONFIG_PATH + "mospred_control.yaml")
    write_cache(data)
    return data

def read_equations_control(control_file=None):
    """
    Reads the equations control file that provides time ranges and
    directory locations for the equation processing.
    """
    # Read file and put it in cache if control_file specified
    if control_file is not None:
        data = read_yaml(control_file)
        write_cache(data)
        return data
    # Otherwise, try to read the cache.
    data = read_cache()
    if data:
        return data
    # If nothing cached, read default control file
    data = read_yaml(CONFIG_PATH + "equations_control.yaml")
    write_cache(data)
    return data

def read_forecast_control(control_file=None):
    """
    Reads the forecast control file that provides time ranges and
    directory locations for the forecast processing.
    """
    # Read file and put it in cache if control_file specified
    if control_file is not None:
        data = read_yaml(control_file)
        write_cache(data)
        return data
    # Otherwise, try to read the cache.
    data = read_cache()
    if data:
        return data
    # If nothing cached, read default control file
    data = read_yaml(CONFIG_PATH + "forecast_control.yaml")
    write_cache(data)
    return data

def read_metar_control():
    """
    Reads the metar control file that provides time ranges and
    directory locations for the observations.
    """
    data = read_cache()
    if data:
        return data
    data = read_yaml(CONFIG_PATH + "metar_control.yaml")
    write_cache(data)
    return data


def read_marine_control():
    """
    Reads the marine control file that provides time ranges and
    directory locations for the observations.
    """
    return read_yaml(CONFIG_PATH + "marine_control.yaml")


def read_grib2_control():
    """
    Reads the grib2 control file that provides
    directory locations for the observations.
    """
    return read_yaml(CONFIG_PATH + "grib2_to_nc_control.yaml")


def read_gfs_tdlpack_lookup():
    """
    Reads and returns mosPlainLanguage > NetCDF variables yaml file.
    """
    return read_yaml(CONFIG_PATH + "mosPlainLanguage_to_nc.yaml")


def read_grib2_lookup():
    """
    Reads and returns the grib2 -> NetCDF variables yaml file.
    """
    return read_yaml(CONFIG_PATH + "grib2_to_nc2.yaml")


def read_mosID_lookup():
    """
    Reads and returns the MOS ID -> NetCDF variables yaml file.
    """
    return read_yaml(CONFIG_PATH + "mosID_to_nc.yaml")


def read_metar_lookup():
    """
    Returns the lookup table for NetCDF -> METAR variables.
    """
    return read_yaml(CONFIG_PATH + "nc_to_metar.yaml")


def read_metar_nc_lookup():
    """
    Returns the lookup table for METAR -> NetCDF variables.
    """
    nc_to_metar = read_metar_lookup()
    out_dict =  {v: k for k, v in nc_to_metar.raw_data.iteritems()}
    return out_dict


def read_marine_lookup():
    """
    Returns the lookup table for METAR -> NetCDF variables.
    """
    nc_to_marine = read_yaml(CONFIG_PATH + "marine_to_nc.yaml")
    out_dict =  {v: k for k, v in nc_to_marine.raw_data.iteritems()}
    return out_dict


def read_observedProperties():
    """
    Returns the set of all observedProperties.
    """
    data = read_cache()
    if data:
        return data
    data = read_yaml(CONFIG_PATH + "ObservedProperties.yaml")
    write_cache(data)
    return data

def read_graphs_control(control_file=None):
    """
    Reads the graphs control file that gives date range, file paths, and lead time
    """
    # Read file and put it in cache if control_file specified
    if control_file is not None:
        data = read_yaml(control_file)
        write_cache(data)
        return data
    # Otherwise, try to read the cache.
    data = read_cache()
    if data:
        return data
    # If nothing cached, read default control file
    data = read_yaml(CONFIG_PATH + "graphs.yaml")
    write_cache(data)
    return data
	
