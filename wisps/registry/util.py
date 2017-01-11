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
    return read_yaml(CONFIG_PATH+"nc_dims.yml")

def read_nc_config():
    """ 
    Read YAML config files to get netcdf structure and properties.
    """
    nc = nc_struct()
    nc.dimensions = read_yaml(CONFIG_PATH+"nc_dims.yml")
    nc.global_attributes = read_yaml(CONFIG_PATH+"nc_globals.yml")
    nc.variables = read_yaml(CONFIG_PATH+"nc_vars.yml")
    return nc

def read_nc_variables():
    """
    returns structured configuration of all WISPS supported variables
    """
    return read_yaml(CONFIG_PATH+"nc_vars.yml")

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

