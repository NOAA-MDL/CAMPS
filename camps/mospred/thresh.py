import os
import sys
import re
import pdb
import operator
from math import *

from . import smooth
from . import interp

"""Module: thresh.py
Changes to a specified value data in a camps data object that satisfy a
simple specified threshold condition.

Methods:
    thresh_setup
    threshold
"""


def thresh_setup(w_obj, operator_str, threshold_value, change_value=1.0):
    """Determines where data meets threshold condition and replaces its value."""

    #Identify the operator in the threshold condition.
    operator_to_func = {
            '>' : operator.gt,
            '<' : operator.lt,
            '>=' : operator.ge,
            '<=' : operator.le,
            '==' : operator.eq,
            '!=' : operator.ne
            }

    if operator_str not in operator_to_func:
        err_str = "operator '" + operator_str + "' cannot be identified"
        raise ValueError(err_str)

    operator_func = operator_to_func[operator_str]

    #Apply threshold condition.
    w_obj.data[operator_func(w_obj.data,threshold_value)] = change_value

    #Denote that this procedure has been applied.
    p = w_obj.add_process('ThreshStep') #Does not indicate threshold condition.

    return w_obj

#Incomplete
#def threshold(arr):
#    """Unneeded as of right now."""
#
#    pass
