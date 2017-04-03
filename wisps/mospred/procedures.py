import os,sys
relative_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__))+"/..")
sys.path.insert(0, relative_path)

from math import *
import re

def example_smooth_func(w_obj, *kwargs):
    pass

def example_map_projection_func(w_obj, *kwargs):
    pass

p = { 
      # Smooth functions
      re.compile(r'smooth (\d).*$') : example_smooth_func,
      re.compile(r'(\d)pt') : example_smooth_func,

      # Map projections
      re.compile(r'lambert') : example_smooth_func,
      re.compile(r'polar') : example_smooth_func,

      # Interpolation 
      re.compile(r'bilinear') : example_smooth_func,
      re.compile(r'spline') : example_smooth_func

    }


def get_procedure(string):
    """Given a procedure string, returns a tuple where 
    element 0 is the function, and element 1 is an array of arguments.
    """
    string = string.lower()
    for key,func in p.iteritems():
        match = key.search(string)
        if match:
            print 'arguments are', match.groups()
            return (func, match.groups)
    # If here, the string has not been matched to a function
    err_msg = string + " cannont be matched to a function"
    raise LookupError(err_msg)


#get_procedure('smooth 9pt')
