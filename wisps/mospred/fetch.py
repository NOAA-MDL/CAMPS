#!/usr/bin/env python
import sys
import os
import parse_pred
import registry.db as db
relative_path = os.path.abspath(
    os.path.dirname(os.path.realpath(__file__)) + "/..")
sys.path.insert(0, relative_path)



def fetch(metadata_dict):
    """
    Given a properly formated metadata dictionary, finds the variable amongst
    the files. If the Observed property is recognized as a variable that needs
    to be computed, then a routine will be started to compute variables.
    """
    for key,value in metadata_dict.iteritems():
        pass



