
import os
import sys
import re
import pdb
relative_path = os.path.abspath(
    os.path.dirname(os.path.realpath(__file__)) + "/..")
sys.path.insert(0, relative_path)
import smooth
import interp
import operator
from math import *
import pdb


def thresh_setup(w_obj, operator_str, threshold_value):
    """
    """
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

    # Set the data where the values are [operator] than [threshold]
    # to the threshold
    w_obj.data[operator_func(w_obj.data,threshold_value)] = threshold_value
    return w_obj

def threshold(arr):
    """Uneeded as of right now. 
    """
    pass
