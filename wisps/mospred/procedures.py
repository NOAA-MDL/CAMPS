import os
import sys
import re
import pdb
relative_path = os.path.abspath(
    os.path.dirname(os.path.realpath(__file__)) + "/..")
sys.path.insert(0, relative_path)
import smooth
import interp
import thresh
from math import *


def smooth_var(w_obj, args):
    if len(w_obj.data.shape) == 3:
        out_arr = smooth.smooth(w_obj.data[:,:,0], args[0])
    else:
        out_arr = smooth.smooth(w_obj.data[:,:], args[0])
    w_obj.data = out_arr
    w_obj.add_process('LinSmooth')


def example_map_projection_func(w_obj, *args):
    pass


p = {
    # Smooth functions
    re.compile(r'smooth (\d*).*$'): smooth_var,

    # Map projections
    re.compile(r'lambert'): smooth_var,
    re.compile(r'polar'): smooth_var,

    # Thresholding
    re.compile(r'thresh.* (.*) (\w*)'): thresh.thresh_setup,

    # Interpolation
    re.compile(r'interp.* (\w*) *$') : interp.interp_setup

}


def get_procedure(string):
    """Given a procedure string, returns a tuple where
    element 0 is the function, and element 1 is an array of arguments.
    """
    string = string.lower()
    for key, func in p.iteritems():
        match = key.search(string)
        if match:
            print 'arguments are', match.groups()
            return (func, match.groups())
    # If here, the string has not been matched to a function
    err_msg = string + " cannont be matched to a function"
    raise LookupError(err_msg)
 
def apply_procedures(variable, procedures):
    """Apply Procedures and return variable
    """
    for p in procedures:
        proc_func, args = get_procedure(p)
        # Execute function
        proc_func(variable, *args)
    return variable





