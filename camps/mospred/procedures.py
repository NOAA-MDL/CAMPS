import os
import sys
import re
import pdb
import logging
from math import *

from . import smooth
from . import interp
from . import thresh
from . import computations


"""Module: procedures.py
This is the procedure clearinghouse.  It connects the request for a process
to the execution of the process.

Methods:
    get_procedure
    apply_procedures
"""


procedures_regex = {
    # Smooth functions
    # match: 'smooth', group(any number of digits), any number of characters, end of line
    re.compile(r'[Ss]mooth (\d*).*$'): smooth.smooth_var,

    # Map projections
    re.compile(r'[Ll]ambert'): None,
    re.compile(r'[Pp]olar'): None,

    # Thresholding
    # match: "thresh", any number of characters, group(any number of characters),
    # group(any word character, 0 or more alpha/num character any number of times, any word char any number of times)
    re.compile(r'[Tt]hresh.* ([<>=].*) \((.*)\).* :.* \((.*)\)'): thresh.thresh_setup,

    # Grid binary
    re.compile(r'[Gg]rid_bin.* ([<>][=]?) ([+-]?\d*\.?\d*)(\s?\w*)') : thresh.grid_binary,

    # Interpolation
    # match: "interp", any character any number of times, group(any word char any number of times),
    # anything then end of line.
    re.compile(r'[Ii]nterp.* (\w*) *$') : interp.interp_setup,

    # Scalar multiplication
    # match: "*", "times", or "multi", group(word character, any number of ".", any number of word characters), anything then end of line
    re.compile(r'\* (\w[\.]*\w*) *$') : computations.multiply,
    re.compile(r'[Tt]imes.* (\w[\.]*\w*) *$') : computations.multiply,
    re.compile(r'[Mm]ult.* [by ]*(\w[\.]*\w*) *$') : computations.multiply,

    # Scalar division
    # match: "/", "divide", group(any number of word characters), anything then end of line
    re.compile(r'\/ (\w*) *$') : computations.divide,
    re.compile(r'[Dd]ivide.* [by]* *(\w[\.]*\w*) *$') : computations.divide,

    # Trig Functions
    re.compile(r'cos') : computations.cos,
    re.compile(r'sin') : computations.sin,
    re.compile(r'tan') : computations.tan,
}


def get_procedure(string):
    """Returns a tuple of process function and its arguments if request is valid.
    Otherwise, execution ceases.
    """

    for key, func in list(procedures_regex.items()):
        match = key.search(string)
        if match:
            log_str = "arguments for " + func.__name__ + " are: " + str(match.groups())
            logging.debug(log_str)
            return (func, match.groups())

    #Stops execution if requested procedure is invalid
    err_msg = string + " cannot be matched to a function"
    raise LookupError(err_msg)


def apply_procedures(variable, procedures, xi_x, xi_y):
    """Apply the procedure to the variable and return the result"""

    log_str = "Applying procedures to \"" + variable.name + '\"'
    logging.info(log_str)
    #loop over the procedures that were passed in from the predictor yaml file
    for p in procedures:
        # Find the procedure function and extract arguments
        # "get_procedure" uses regular expression matching to determine which
        # of the allowed procedures to apply to the variable object
        proc_func, args = get_procedure(p)
        # Execute the procedure function.
        if proc_func==interp.interp_setup:
            proc_func(variable, xi_x, xi_y, *args) #interpolation requires grid coordinates
        else:
            proc_func(variable, *args)

    return variable
