import sys
import os
file_dir = os.path.dirname(os.path.realpath(__file__))
relative_path = "/.."
path = os.path.abspath(file_dir + relative_path)
sys.path.insert(0, path)
import registry.db.db as db
import data_mgmt.reader as reader
import pdb


def fetch(metadata_dict, time=None, lead_time=None):
    """
    Given a properly formated metadata dictionary, finds the variable amongst
    the files. If the Observed property is recognized as a variable that needs
    to be computed, then a routine will be started to compute variables.
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
        # Calculate it?
        return None
    elif num_records_returned == 1:
        record = ret[0]
        print record
        return reader.read_var(record['filename'], record['name'])
    
    


def find_date():
    pass



