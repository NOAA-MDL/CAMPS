import sys
import os
import logging
import inspect
import yaml
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


def read_yaml(filename):
    """Reads the contents of a yaml file and returns the value."""
    logging.info("reading yaml config. File: " + filename)
    try:
        with open(filename, 'r') as stream:
            try:
                structured_data = yaml.load(stream)
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
    """checks whether the function's data has been chached or not.
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
    func_name = inspect.currentframe().f_back.f_code.co_name
    _cache[func_name] = data


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


def read_variables():
    """
    returns structured configuration of all WISPS supported variables.
    """
    return read_nc_meta()['variables']


def read_nc_meta():
    """Reads netcdf.yml file that contains the metadata for
    common variables.
    """
    data = read_cache()
    if data:
        return data
    data = read_yaml(CONFIG_PATH + "netcdf.yml")
    write_cache(data)
    return data

def read_procedures():
    """Reads netcdf.yml file that contains the metadata for
    common variables.
    """
    data = read_cache()
    if data:
        return data
    data = read_yaml(CONFIG_PATH + "procedures.yml")
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
    # Otherwise, try to read the cache.
    data = read_cache()
    if data:
        return data
    # If nothing cached, read default control file
    data = read_yaml(CONFIG_PATH + "mospred_control.yml")
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
    data = read_yaml(CONFIG_PATH + "metar_control.yml")
    write_cache(data)
    return data


def read_marine_control():
    """
    Reads the marine control file that provides time ranges and
    directory locations for the observations.
    """
    return read_yaml(CONFIG_PATH + "marine_control.yml")


def read_grib2_control():
    """
    Reads the grib2 control file that provides
    directory locations for the observations.
    """
    return read_yaml(CONFIG_PATH + "grib2_control.yml")


def read_gfs_tdlpack_lookup():
    """
    Reads and returns mosPlainLanguage > NetCDF variables yaml file.
    """
    return read_yaml(CONFIG_PATH + "mosPlainLanguage_to_nc.yml")


def read_grib2_lookup():
    """
    Reads and returns the grib2 -> NetCDF variables yaml file.
    """
    return read_yaml(CONFIG_PATH + "grib2_to_nc.yml")


def read_mosID_lookup():
    """
    Reads and returns the MOS ID -> NetCDF variables yaml file.
    """
    return read_yaml(CONFIG_PATH + "mosID_to_nc.yml")


def read_metar_lookup():
    """
    Returns the lookup table for NetCDF -> METAR variables.
    """
    return read_yaml(CONFIG_PATH + "nc_to_metar.yml")


def read_metar_nc_lookup():
    """
    Returns the lookup table for METAR -> NetCDF variables.
    """
    nc_to_metar = read_metar_lookup()
    return {v: k for k, v in nc_to_metar.iteritems()}


def read_marine_lookup():
    """
    Returns the lookup table for METAR -> NetCDF variables.
    """
    return read_yaml(CONFIG_PATH + "marine_to_nc.yml")


def read_observedProperties():
    """
    Returns the set of all observedProperties.
    """
    return read_yaml(CONFIG_PATH + "ObservedProperties.yml")
