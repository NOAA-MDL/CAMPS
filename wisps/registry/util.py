import logging
import yaml
import sys
import os
"""
Module that abstracts the reading of the yaml configuration file held in config directory
"""

class nc_struct():
    def __init__(self):
        self.dimensions = {}
        self.global_attributes = {}
        self.variables = {}

CONFIG_PATH = os.path.dirname(os.path.realpath(__file__)) + "/"
def read_yaml(filename):
    """Reads the contents of a yaml file and returns the value"""
    logging.info("reading yaml config. Filename: "+filename)
    try:
        with open(filename, 'r') as stream:
            try:
                structured_data = yaml.load(stream)
                return structured_data
            except yaml.YAMLError as err:
                logging.error("YAML cannot parse input")
                logging.error("Error:\n" )
                logging.error(err)
                raise
    except IOError as err:
        logging.error("File cannot be read. It may not exist, or cannot be read")
        logging.error("Error:" + str(err))
        raise


def read_dimensions():
    """
    Reads and returns dimension definitions
    """
    nc_struct = read_yaml(CONFIG_PATH+"netcdf.yml")
    # Just get the variables
    return nc_struct['dimensions']

def read_globals():
    """
    Reads and returns global attributes definitions
    """
    nc_struct = read_yaml(CONFIG_PATH+"netcdf.yml")
    # Just get the variables
    return nc_struct['globals']

def read_nc_config():
    """ 
    Read YAML config files to get netcdf structure and properties.
    """
    nc = nc_struct()
    nc.dimensions = read_dimensions()
    nc.global_attributes = read_globals()
    nc.variables = read_variables()
    return nc

def read_variables():
    """
    returns structured configuration of all WISPS supported variables
    """
    nc_struct = read_yaml(CONFIG_PATH+"netcdf.yml")
    # Just get the variables
    return nc_struct['variables']

def read_metar_control():
    """
    Reads the metar control file that provides time ranges and 
    directory locations for the observations.
    """
    return read_yaml(CONFIG_PATH+"metar_control_file.yml")

def read_marine_control():
    """
    Reads the marine control file that provides time ranges and 
    directory locations for the observations.
    """
    return read_yaml(CONFIG_PATH+"marine_control_file.yml")

def read_mosID_lookup():
    """
    Reads and returns the MOS ID -> NetCDF variables yaml file.
    """
    return read_yaml(CONFIG_PATH+"mosID_to_nc.yml")

def read_metar_lookup():
    """ 
    Returns the lookup table for METAR -> NetCDF variables.
    """
    return read_yaml(CONFIG_PATH+"nc_to_metar.yml")

def read_marine_lookup():
    """ 
    Returns the lookup table for METAR -> NetCDF variables.
    """
    return read_yaml(CONFIG_PATH+"marine_to_nc.yml")

nc_to_metar = read_metar_lookup()
metar_to_nc = {v: k for k, v in nc_to_metar.iteritems()}

