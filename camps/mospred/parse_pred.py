import os
import sys
import re
import pdb
import logging

from ..registry import util as cfg
from . import procedures


"""Module: parse_pred.py
Extracts from input strings and returns relevant information about predictors.

Methods:
    str2epoch
    check_valid_keys
    separate_entries
    get_time_multiplier
    cell_method
    duration
    observedProperty
    lead_time
    forecast_ref_time
    vertical_coordinate
    source
"""


observedProperties = cfg.read_observedProperties()
default_time = 'hour'
cell_methods_regex = {
    re.compile(".*av[a-z]*g.*"): 'mean',
    re.compile(".*mean.*"): 'mean',
    re.compile(".*diff.*"): 'difference',
    re.compile(".*sum.*"): 'sum',
    re.compile(".*point.*"): 'point',
    re.compile(".*max.*"): 'maximum',
    re.compile(".*min.*"): 'minimum',
    re.compile(".*mid.*"): 'mid_range',
    re.compile(".*st[a-z]*d.*dev*"): 'standard_deviation',
    re.compile(".*var.*"): 'variance',
    re.compile(".*thick.*"): 'PressThickness', # Added this to get thickness to point to proper function for thickness calculation...revisit
    re.compile(".*lapse.*"): 'TempLapse' # Added this to get lapse to point to proper function for lapse calculation...revisit
}

time_mult = {
    re.compile("s.*"): 3600,  # seconds
    re.compile("m.*"): 60,
    re.compile("h.*"): 1,
    re.compile("d.*"): 24,
}

#Incomplete
#def str2epoch(in_str):
#    """Converts a date string to epoch time in seconds """
#
#    if type(in_str) is not str:
#        pass


def check_valid_keys(in_dict):
    """Stops execution if a key in the predictor dictionary is not
    in the limited set of valid keys.
    """

    valid_keys = set([
        'Vertical_Coordinate',
        'Duration',
        'Source',
        'LeadTime',
        'property',
        'Procedure'
            ])

    for k in list(in_dict.keys()):
        try:  
            assert k in valid_keys
        except AssertionError:
            logging.error( str(k) + " is not a valid key")
            logging.error("valid keys are:\n" + ",\n".join(valid_keys))
            raise


def separate_entries(in_str):
    """Seperates terms of a time string of the format
    '(number)(time units) (period method)' and returns a
    dictionary with key/value pairs of time in seconds and,
    if available, cell (period) method.
    """

    in_str = str(in_str) #Convert to a string if not already
    exp = re.compile("^ *(\d+) *([A-Za-z]*) *([a-z]*)")
    out = exp.match(in_str)
    if not out:
        err_str = "string, '" + in_str + "' cannot be parsed"
        raise LookupError(err_str)
    # Process the groups, where group index
    # 0 corresponds to the time,
    # 1 to the unit of time, and
    # 2 to the cell method
    groups = list(out.groups())
    groups[0] = int(groups[0])
    #Convert time value to that in seconds
    if len(groups) >= 2:
        mult = get_time_multiplier(groups[1])
        if mult == 24:
            time = groups[0] * mult
        else:
            time = int(groups[0]/mult)
    #Check if cell method exists and is valid
    if len(groups) == 3 and groups[2]:
        cell_method_name = cell_method(groups[2]) #'None' if not valid
        return {'time': time, 'cell_method': cell_method_name}

    return {'time': time}


def get_time_multiplier(time_unit):
    """Returns a multiplier to convert time to seconds"""

    time_unit = time_unit.lower()
    for regex, mult in list(time_mult.items()):
        if regex.match(time_unit):
            return mult

    return 1


def cell_method(in_str):
    """Matches in_str with a CF convention cell method.
    Returns None if no match.
    """

    in_str = in_str.lower()
    for regex, cell_method in list(cell_methods_regex.items()):
        if regex.match(in_str):
            return cell_method

    return None


def duration(in_str):
    """Returns a duration identifier."""

    entries = separate_entries(in_str)

    return entries



def observedProperty(in_str):
    """Stops execution if the observed property in in_str is invalid"""

    try:
        return observedProperties[in_str]
    except KeyError:
        err_str = in_str + " is not a valid observedProperty"
        logging.error(err_str)
        raise


def lead_time(in_str):
    """Converts lead time assumed in string in_str to integer value in seconds"""

    return separate_entries(in_str)['time']

#Incomplete
#def forecast_ref_time(in_str):
#    """Given a forecast reference Time, return a number of seconds since
#    the epoch.
#    """
#
#    return separate_entries(in_str)


def vertical_coordinate(in_str):
    """Parses the string in_str assuming it gives the
    predictor's vertical coordinates and returns the gleaned
    relevant information via a dictionary vertical_dict.
    If the vertical coordinate is a level, the keys are
    'layer1' and 'units'.  If a layer, additional keys are
    'layer2' and 'cell_method'.
    """

    #Process the input string.
    in_str = str(in_str)
    in_str = in_str.strip(" ")

    #Create the dictionary to be filled in and returned.
    vertical_dict = {}

    #Consider the special case of the Earth surface
    if in_str == '0':
        vertical_dict['layer1'] = 0
        vertical_dict['units'] = 'm'
        return vertical_dict

    #Identify the character seperating the coordinate values of the
    #bottom and top levels of a layer.
    sep = None
    if "to" in in_str:
        sep = "to"
    if "-" in in_str:
        sep = '-'
    single_layered = sep is None
    multi_layered = sep is not None

    #Write into the dictionary depending on whethet the vertical structure
    #is a layer or a level.
    if multi_layered:
        #Split string by space and identify the last element to be the cell method.
        in_str_arr = in_str.split(" ")
        cell_method_name = cell_method(in_str_arr[-1])
        assert cell_method_name is not None #Stop execution if cell method is invalid
        #Join the remaining parts and then separate by sep to identify levels.
        in_str = "".join(in_str_arr[0:-1])
        in_str_arr = in_str.split(sep)
        assert len(in_str_arr) == 2 #Stop execution if the number of levels exceeds two.
        exp = re.compile("^ *(\d+) *([a-zA-Z]*)") #pattern of level string
        layer1 = exp.match(in_str_arr[0]).groups()
        layer2 = exp.match(in_str_arr[1]).groups()
        if layer1[1]:
            units = layer1[1]
        elif layer2[1]:
            units = layer2[1]
        else:
            raise LookupError("units in Vertical_Coordinate not defined")
        vertical_dict['layer1'] = int(layer1[0]) #coordinate value of first level
        vertical_dict['layer2'] = int(layer2[0]) #coordinate value of second level
        vertical_dict['units'] = units
        vertical_dict['cell_method'] = cell_method_name

    elif single_layered:
        exp = re.compile("^ *(\d+) *([a-zA-Z]*) *")
        layer = exp.match(in_str).groups()
        if len(layer) <= 1 or not layer[1]:
            raise LookupError("units in Vertical_Coordinate not defined")
        vertical_dict['layer1'] = int(layer[0])
        vertical_dict['units'] = layer[1]

    return vertical_dict


def source(in_str):
    """Stops execution if source of data is invalid"""

    in_str = in_str.lower()
    valid_sources = ['metar', 'gfs', 'gfs13', 'nam', 'mesonet']
    if in_str in valid_sources:
        return True

    raise LookupError
