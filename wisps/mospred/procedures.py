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
import computations
from math import *



procedures_regex = {
    # Smooth functions
    re.compile(r'smooth (\d*).*$'): smooth.smooth_var,

    # Map projections
    re.compile(r'lambert'): None,
    re.compile(r'polar'): None,

    # Thresholding
    re.compile(r'thresh.* (.*) (\w*)'): thresh.thresh_setup,

    # Interpolation
    re.compile(r'interp.* (\w*) *$') : interp.interp_setup,

    # Scalar multiplication
    re.compile(r'\* (\w*) *$|times.* (\w*) *$|mult.* [by]* *(\w*) *$') : computations.multiply,

    # Scalar division
    re.compile(r'\/ (\w*) *$|divide.* (\w*) *$|divide.* [by]* *(\w*) *$') : ccomputations.divide,

    # Trig
    re.compile(r'cos') : computations.cos,
    re.compile(r'sin') : computations.sin,
    re.compile(r'tan') : computations.tan,


}


def get_procedure(string):
    """Given a procedure string, returns a tuple where
    element 0 is the function, and element 1 is an array of arguments.
    """
    string = string.lower()
    for key, func in procedures_regex.iteritems():
        match = key.search(string)
        if match:
            print 'arguments are', match.groups()
            return (func, match.groups())
    # If here, the string has not been matched to a function
    err_msg = string + " cannot be matched to a function"
    raise LookupError(err_msg)
 
def apply_procedures(variable, procedures):
    """Apply Procedures and return variable
    """
    for p in procedures:
        proc_func, args = get_procedure(p)
        # Execute function
        proc_func(variable, *args)
    return variable





