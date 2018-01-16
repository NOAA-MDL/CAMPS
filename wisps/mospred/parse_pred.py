import os
import sys
import re
import pdb
relative_path = os.path.abspath(
    os.path.dirname(os.path.realpath(__file__)) + "/..")
sys.path.insert(0, relative_path)
import registry.util as cfg
import procedures

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
    re.compile(".*var.*"): 'variance'
}

time_mult = {
    re.compile("s.*"): 1,  # seconds
    re.compile("m.*"): 60,
    re.compile("h.*"): 3600,
    re.compile("d.*"): 86400,
}


def str2epoch(in_str):
    if type(in_str) is not str:
        pass
        # Assumes hours

def check_valid_keys(in_dict):
    valid_keys = set([
        'Vertical_Coordinate',
        'Duration',
        'Source',
        'LeadTime',
        'Property',
        'Procedure'
            ])
    for k in in_dict.keys():
        try:  
            assert k in valid_keys
        except AssertionError:
            print k, "not a valid key"
            print "valid keys are:\n", ",\n".join(valid_keys)
            raise


def separate_entries(in_str):
    """
    Attempts to seperate different entries.
    Returns a tuple of time and cell method if available.
    """
    exp = re.compile("^ *(\d+) *([A-Za-z]*) *([a-z]*)")
    out = exp.match(in_str)
    if not out:
        err_str = "string, '" + in_str + "' cannot be parsed"
        raise LookupError(err_str)
    # Process the groups, where group
    # 1 is the time,
    # 2 is the unit of time,
    # 3 is the cell method
    groups = list(out.groups())
    groups[0] = int(groups[0])
    if len(groups) >= 2:
        mult = get_time_multiplier(groups[1])
        time = groups[0] * mult
    if len(groups) == 3 and groups[2]:
        cell_method_name = cell_method(groups[2])
        return {'time': time, 'cell_method': cell_method_name}
    return {'time': time}


def get_time_multiplier(in_str):
    in_str = in_str.lower()
    for regex, mult in time_mult.iteritems():
        if regex.match(in_str):
            return mult
    return None


def cell_method(in_str):
    """Matches in_str with a common representation
    of CF convention cell methods.
    """
    in_str = in_str.lower()
    for regex, cell_method in cell_methods_regex.iteritems():
        if regex.match(in_str):
            return cell_method
    return None


def duration(in_str):
    """Returns a duration identifier."""
    entries = separate_entries(in_str)
    return entries


def observedProperty(in_str):
    """Try to find the observedProperty. If found, return
    full observedProperty path"""
    try:
        return observedProperties[in_str]
    except KeyError:
        err_str = in_str + " is not a valid observedProperty"
        print err_str
        raise


def lead_time(in_str):
    """Given unformatted lead_time string, return number of seconds of leadTime.
    """
    return separate_entries(in_str)['time']


def forecast_ref_time(in_str):
    """Given a forecast reference Time, return a number of seconds since
    the epoch.
    """
    return separate_entries(in_str)


def vertical_coordinate(in_str):
    """Parses the vertical coordinate string.
    returns a dict, where:
    layer1 - first layer
    layer2 - second layer (if applicable)
    unit - unit of measurement
    cell_method - cell method if it's multi layered
    """
    in_str = str(in_str)
    in_str = in_str.lower()
    in_str = in_str.strip(" ")  # take off leading or following spaces
    vertical_dict = {}
    if in_str == '0':
        vertical_dict['layer1'] = 0
        vertical_dict['units'] = 'm'
        return vertical_dict
    sep = None
    if "to" in in_str:
        sep = "to"
    if "-" in in_str:
        sep = '-'
    single_layered = sep is None
    multi_layered = sep is not None

    if multi_layered:  
        in_str_arr = in_str.split(" ")  # get cell method.
        # It should be in the last position
        cell_method_name = cell_method(in_str_arr[-1])
        assert cell_method_name is not None
        in_str = "".join(in_str_arr[0:-1])
        in_str_arr = in_str.split(sep)
        exp = re.compile("^ *(\d+) *([a-z]*)")
        assert len(in_str_arr) == 2
        layer1 = exp.match(in_str_arr[0]).groups()
        layer2 = exp.match(in_str_arr[1]).groups()
        if layer1[1]:
            units = layer1[1]
        elif layer2[1]:
            units = layer2[1]
        else:
            raise LookupError("units in Vertical_Coordinate not defined")
        vertical_dict['layer1'] = int(layer1[0])
        vertical_dict['layer2'] = int(layer2[0])
        vertical_dict['units'] = units
        vertical_dict['cell_method'] = cell_method_name

    elif single_layered: 
        exp = re.compile("^ *(\d+) *([a-z]*) *")
        layer = exp.match(in_str).groups()
        if len(layer) <= 1 or not layer[1]:
            raise LookupError("units in Vertical_Coordinate not defined")
        vertical_dict['layer1'] = int(layer[0])
        vertical_dict['units'] = layer[1]

    return vertical_dict


def source(in_str):
    """returns the source attribute in the mos predictor list"""
    in_str = in_str.lower()
    valid_sources = ['metar', 'gfs', 'gfs13', 'nam', 'mesonet']
    if in_str in valid_sources:
        return True
    raise LookupError
