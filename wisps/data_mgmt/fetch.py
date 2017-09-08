import sys
import os
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
import registry.db.db as db
import data_mgmt.reader as reader
import pdb
from os.path import basename


def fetch(time=None, lead_time=None, **metadata_dict):
    r"""
    Given a properly formated metadata dictionary, finds the variable amongst
    the files. If the Observed property is recognized as a variable that needs
    to be computed, then a routine will be started to compute variables.
    
    Metadata Keys w/ type:
     'property'        : str
     'source'          : str
     'start'           : int
     'end'             : int
     'duration'        : int
     'duration_method' : str
     'vert_coord1'     : int
     'vert_coord2'     : int
     'vert_method'     : str
    """
    # First check if calling the database gives any entries.
    ret = db.get_variable(**metadata_dict)
    num_records_returned = len(ret)
    if num_records_returned > 1:
        if len(ret) < 5:
            print "Variables returned:"
            for i in ret:
                print i
        print len(ret), "variables returned from fetch."
        print "Please be more specific"
        raise RuntimeError("too many variables returned")
    elif num_records_returned  == 0:
        # Check if another fetch without full URI might yeild results
        if 'property' in metadata_dict:
            prop = metadata_dict['property']
            prop_basename = basename(prop)
            if prop != prop_basename:
                metadata_dict['property'] = prop_basename
                return fetch(time=time,lead_time=lead_time,**metadata_dict)
        # Otherwise return that nothing was found
        return None
    elif num_records_returned == 1:
        record = ret[0]
        print "Found one Matching record."
        filepath = record['filename']
        nc_variable_name = record['name']
        return reader.read_var(filepath, nc_variable_name, lead_time, time)


def find_date():
    pass

def printdict(dict):
    for k,v in dict.iteritems():
        print str(k) + " : " + str(v)


